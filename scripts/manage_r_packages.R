#!/usr/bin/env Rscript
# Usage: Rscript scripts/manage_r_packages.R [--component NAME] [--apply]
# Default is check-only. Applying changes requires --apply and saved consent in
# ~/.fiskwise/config.json; R_AW_INSTALL_MISSING=false and renv always block it.

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_args <- function(args) {
  apply <- "--apply" %in% args
  component <- NULL
  i <- 1L
  while (i <= length(args)) {
    arg <- args[[i]]
    if (arg == "--apply") {
      i <- i + 1L
    } else if (arg == "--component") {
      if (i == length(args) || startsWith(args[[i + 1L]], "--")) stop("--component needs a name.", call. = FALSE)
      component <- args[[i + 1L]]
      i <- i + 2L
    } else if (grepl("^--component=.+$", arg)) {
      component <- sub("^--component=", "", arg)
      i <- i + 1L
    } else stop("Unknown argument: ", arg, call. = FALSE)
  }
  list(apply = apply, component = component)
}

component_order <- function(inventory, requested) {
  by_name <- setNames(inventory, vapply(inventory, `[[`, "", "name"))
  result <- character()
  visit <- function(name) {
    if (name %in% result || identical(name, "fiskwise")) return(invisible(NULL))
    item <- by_name[[name]]
    if (is.null(item)) stop("Unknown component in registry: ", name, call. = FALSE)
    if (!identical(item$status, "available")) return(invisible(NULL))
    result <<- c(result, name)
    for (dependency in item$dependencies %||% list()) visit(dependency)
    invisible(NULL)
  }
  for (name in requested) visit(name)
  result
}

managed_packages <- function(inventory, registry, component = NULL) {
  by_name <- setNames(inventory, vapply(inventory, `[[`, "", "name"))
  requested <- if (!is.null(component)) component else names(registry$components %||% list())
  requested <- setdiff(requested, "fiskwise")
  if (!length(requested)) {
    requested <- vapply(Filter(function(p) identical(p$kind, "knowledge") && isTRUE(p$core) &&
                                 identical(p$status, "available"), inventory), `[[`, "", "name")
  }
  selected <- component_order(inventory, requested)
  # Core R-package components have managed inventories independently of knowledge-pack installation.
  selected <- unique(c(selected, vapply(Filter(function(p) identical(p$kind, "r") && isTRUE(p$core) &&
                                                  identical(p$status, "available"), inventory), `[[`, "", "name")))
  packages <- list()
  for (name in selected) {
    entry <- by_name[[name]]
    if (is.null(entry) || !identical(entry$status, "available")) next
    entries <- c(entry$r_packages %||% list(), if (!is.null(entry$r_package)) list(entry$r_package) else list())
    for (pkg in entries) {
      pkg$component <- name
      packages[[length(packages) + 1L]] <- pkg
    }
  }
  if (!length(packages)) return(list())
  package_names <- vapply(packages, function(pkg) as.character(pkg$name %||% ""), character(1L))
  packages <- packages[nzchar(package_names)]
  names(packages) <- package_names[nzchar(package_names)]
  packages[!duplicated(names(packages))]
}

cran_repo_options <- function(repos = getOption("repos")) {
  if (is.null(repos) || !length(repos)) repos <- c(CRAN = "https://cloud.r-project.org")
  repos[is.na(repos) | repos == "@CRAN@"] <- "https://cloud.r-project.org"
  repos
}

renv_project <- function(path = getwd()) {
  current <- normalizePath(path, mustWork = TRUE)
  repeat {
    if (file.exists(file.path(current, "renv.lock")) || dir.exists(file.path(current, "renv"))) return(TRUE)
    parent <- dirname(current)
    if (identical(parent, current)) return(FALSE)
    current <- parent
  }
}

existing_user_library <- function(value = Sys.getenv("R_LIBS_USER", unset = "")) {
  candidates <- strsplit(value, .Platform$path.sep, fixed = TRUE)[[1L]]
  candidates <- path.expand(candidates[nzchar(candidates)])
  candidates <- candidates[dir.exists(candidates)]
  writable <- candidates[file.access(candidates, 2L) == 0L]
  if (length(writable)) writable[[1L]] else ""
}

installation_permitted <- function(apply, consent, env_value, in_renv, user_lib, dependencies_known = TRUE) {
  isTRUE(apply) && !identical(tolower(env_value %||% ""), "false") &&
    isTRUE(consent) && !isTRUE(in_renv) && nzchar(user_lib) && isTRUE(dependencies_known)
}

package_dependencies <- function(index, names) {
  # Only runtime dependencies are in scope; Suggests and Enhances are excluded.
  result <- character()
  fields <- c("Depends", "Imports", "LinkingTo")
  for (name in names) {
    if (!name %in% rownames(index)) next
    for (field in fields) {
      value <- index[name, field]
      if (length(value) && !is.na(value) && nzchar(value)) {
        deps <- trimws(strsplit(value, ",", fixed = TRUE)[[1L]])
        deps <- sub("\\s*\\(.*$", "", deps)
        result <- c(result, deps[deps %in% rownames(index)])
      }
    }
  }
  unique(setdiff(result, c(names, "R")))
}

expand_cran_packages <- function(packages, index) {
  entries <- packages
  seen <- names(entries)
  frontier <- names(Filter(function(p) identical(p$source %||% "CRAN", "CRAN") ||
                             identical(p$source, "@CRAN@"), entries))
  while (length(frontier)) {
    deps <- setdiff(package_dependencies(index, frontier), seen)
    if (!length(deps)) break
    for (name in deps) entries[[name]] <- list(name = name, source = "CRAN", ref = "default", component = "dependency")
    seen <- c(seen, deps)
    frontier <- deps
  }
  entries
}

github_sha <- function(source, ref = "HEAD") {
  if (!grepl("^[^/]+/[^/]+$", source)) return(NA_character_)
  endpoint <- sprintf("https://api.github.com/repos/%s/commits/%s", source, utils::URLencode(ref, reserved = TRUE))
  old_timeout <- options(timeout = min(getOption("timeout"), 8L))
  on.exit(options(old_timeout), add = TRUE)
  tryCatch(as.character(jsonlite::fromJSON(endpoint, simplifyVector = TRUE)$sha), error = function(e) NA_character_)
}

memoize_github_sha <- function(lookup = github_sha) {
  cache <- new.env(parent = emptyenv())
  function(source, ref) {
    key <- paste(source, ref, sep = "@")
    if (!exists(key, envir = cache, inherits = FALSE)) cache[[key]] <- lookup(source, ref)
    cache[[key]]
  }
}

github_description_url <- function(source, sha, subdir = NULL) {
  if (length(sha) != 1L || is.na(sha) || !grepl("^[0-9a-fA-F]{7,40}$", sha)) return(NA_character_)
  path <- c(if (!is.null(subdir) && nzchar(subdir)) strsplit(subdir, "/", fixed = TRUE)[[1L]] else character(), "DESCRIPTION")
  path <- paste(vapply(path, utils::URLencode, character(1L), reserved = FALSE), collapse = "/")
  sprintf("https://raw.githubusercontent.com/%s/%s/%s", source, sha, path)
}

read_github_description <- function(source, sha, subdir = NULL) {
  endpoint <- github_description_url(source, sha, subdir)
  if (is.na(endpoint)) return(NULL)
  old_timeout <- options(timeout = min(getOption("timeout"), 8L))
  on.exit(options(old_timeout), add = TRUE)
  connection <- tryCatch(url(endpoint, open = "r"), error = function(e) NULL)
  if (is.null(connection)) return(NULL)
  on.exit(close(connection), add = TRUE)
  tryCatch(paste(readLines(connection, warn = FALSE), collapse = "\n"), error = function(e) NULL)
}

parse_description <- function(text) {
  if (is.null(text) || !length(text) || !nzchar(text)) return(NULL)
  connection <- textConnection(text)
  on.exit(close(connection), add = TRUE)
  tryCatch(as.list(read.dcf(connection)[1L, , drop = TRUE]), error = function(e) NULL)
}

description_runtime_dependencies <- function(description) {
  fields <- c("Depends", "Imports", "LinkingTo")
  values <- unlist(description[intersect(fields, names(description))], use.names = FALSE)
  if (!length(values)) return(character())
  dependencies <- unlist(strsplit(values, ",", fixed = TRUE), use.names = FALSE)
  dependencies <- trimws(sub("\\s*\\(.*$", "", dependencies))
  unique(setdiff(dependencies[nzchar(dependencies)], "R"))
}

description_github_remotes <- function(description) {
  remotes <- description$Remotes %||% ""
  if (!nzchar(remotes)) return(list())
  specs <- trimws(strsplit(remotes, ",", fixed = TRUE)[[1L]])
  result <- list()
  for (spec in specs) {
    pieces <- strsplit(spec, "=", fixed = TRUE)[[1L]]
    if (length(pieces) == 2L) {
      package <- trimws(pieces[[1L]])
      remote <- trimws(pieces[[2L]])
    } else {
      remote <- trimws(spec)
      package <- sub(".*/", "", sub("@.*$", "", remote))
    }
    remote <- sub("^github::", "", remote)
    remote <- sub("^https://github.com/", "", remote)
    ref <- if (grepl("@", remote, fixed = TRUE)) sub("^[^@]+@", "", remote) else "default"
    source <- sub("@.*$", "", remote)
    if (grepl("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", source)) {
      result[[package]] <- list(name = package, source = source, ref = ref)
    }
  }
  result
}

expand_github_packages <- function(packages, cran_index, sha_lookup = github_sha,
                                   description_lookup = read_github_description,
                                   installed_lookup = installed_package,
                                   installed_description_lookup = installed_description,
                                   base_packages = rownames(utils::installed.packages(priority = c("base", "recommended")))) {
  entries <- packages
  seen <- names(entries)
  pending <- Filter(function(pkg) !identical(pkg$source %||% "CRAN", "CRAN") && !identical(pkg$source, "@CRAN@"), entries)
  unknown <- character()
  while (length(pending)) {
    pkg <- pending[[1L]]
    pending <- pending[-1L]
    ref <- pkg$ref %||% "default"
    installed <- installed_lookup(pkg$name)
    checked_sha <- if (identical(ref, "preserve-installed")) {
      if (is.null(installed)) NA_character_ else as.character(installed$remote_sha %||% NA_character_)
    } else sha_lookup(pkg$source, if (identical(ref, "default")) "HEAD" else ref)
    description_text <- if (!is.na(checked_sha)) description_lookup(pkg$source, checked_sha, pkg$subdir %||% NULL) else NULL
    description <- parse_description(description_text)
    installed_fallback_stale <- FALSE
    if (is.null(description) && !is.null(installed)) {
      installed_desc <- installed_description_lookup(pkg$name)
      if (!is.null(installed_desc)) {
        description <- as.list(installed_desc)
        installed_sha <- as.character(installed$remote_sha %||% NA_character_)
        installed_fallback_stale <- !is.na(checked_sha) &&
          (is.na(installed_sha) || !identical(tolower(installed_sha), tolower(checked_sha)))
      }
    }
    if (is.null(description)) {
      unknown <- c(unknown, paste0(pkg$name, " (GitHub DESCRIPTION unavailable)"))
      next
    }
    if (installed_fallback_stale) unknown <- c(unknown, paste0(pkg$name, " (installed DESCRIPTION is not for checked GitHub SHA)"))
    runtime_dependencies <- description_runtime_dependencies(description)
    remotes <- description_github_remotes(description)
    for (dependency in runtime_dependencies) {
      if (dependency %in% base_packages || dependency %in% seen) next
      if (!is.null(remotes[[dependency]])) {
        entry <- remotes[[dependency]]
        entry$component <- paste0(pkg$name, " dependency")
        entries[[dependency]] <- entry
        seen <- c(seen, dependency)
        pending[[length(pending) + 1L]] <- entry
        next
      }
      if (dependency %in% rownames(cran_index)) {
        entry <- list(name = dependency, source = "CRAN", ref = "default", component = paste0(pkg$name, " dependency"))
        entries[[dependency]] <- entry
        seen <- c(seen, dependency)
        next
      }
      dependency_installed <- installed_lookup(dependency)
      if (!is.null(dependency_installed)) {
        remote_owner <- dependency_installed$remote_username %||% ""
        remote_repo <- dependency_installed$remote_repo %||% ""
        if (nzchar(remote_owner) && nzchar(remote_repo)) {
          entry <- list(name = dependency, source = paste(remote_owner, remote_repo, sep = "/"),
                        ref = dependency_installed$remote_ref %||% "preserve-installed", component = paste0(pkg$name, " dependency"))
          entries[[dependency]] <- entry
          seen <- c(seen, dependency)
          pending[[length(pending) + 1L]] <- entry
          next
        }
      }
      unknown <- c(unknown, paste0(pkg$name, " requires unresolved runtime dependency ", dependency))
    }
  }
  list(packages = entries, unknown = unique(unknown))
}

# packageDescription() returns NA with a warning, not an error, for a missing package.
installed_description <- function(name) {
  desc <- tryCatch(suppressWarnings(utils::packageDescription(name, lib.loc = .libPaths())),
                   error = function(e) NULL)
  if (!is.list(desc)) NULL else desc
}

installed_package <- function(name) {
  desc <- installed_description(name)
  if (is.null(desc)) return(NULL)
  list(version = as.character(desc$Version), remote_sha = as.character(desc$RemoteSha %||% NA_character_),
       remote_ref = as.character(desc$RemoteRef %||% NA_character_),
       remote_username = as.character(desc$RemoteUsername %||% ""),
       remote_repo = as.character(desc$RemoteRepo %||% ""))
}

package_status <- function(pkg, installed, cran_index, sha_lookup = github_sha) {
  source <- pkg$source %||% "CRAN"
  name <- pkg$name
  if (source %in% c("CRAN", "@CRAN@")) {
    latest <- if (name %in% rownames(cran_index)) as.character(cran_index[name, "Version"]) else NA_character_
    state <- if (is.null(installed)) "missing" else if (!is.na(latest) && utils::compareVersion(installed$version, latest) < 0L) "outdated" else if (is.na(latest)) "installed; latest unknown" else "current"
    return(list(source = "CRAN", state = state, latest = latest))
  }
  ref <- pkg$ref %||% "default"
  if (identical(ref, "preserve-installed")) {
    return(list(source = "GitHub", state = if (is.null(installed)) "missing; no ref selected" else "custom pin preserved",
                latest_sha = NA_character_, preserve = TRUE))
  }
  installed_ref <- if (is.null(installed)) NA_character_ else as.character(installed$remote_ref %||% NA_character_)
  if (identical(ref, "default") && !is.na(installed_ref) && nzchar(installed_ref) &&
      !installed_ref %in% c("HEAD", "default")) {
    return(list(source = "GitHub", state = "custom pin preserved", latest_sha = NA_character_, preserve = TRUE))
  }
  sha <- sha_lookup(source, if (identical(ref, "default")) "HEAD" else ref)
  installed_sha <- if (is.null(installed)) NA_character_ else as.character(installed$remote_sha %||% NA_character_)
  same <- !is.null(installed) && !is.na(sha) && !is.na(installed_sha) && identical(tolower(installed_sha), tolower(sha))
  list(source = "GitHub", state = if (is.null(installed)) "missing" else if (is.na(sha)) "installed; SHA unknown" else if (same) "current" else "SHA differs",
       latest_sha = sha, same = same, ref = ref)
}

# Recognize only our own verified SHA installs; preserve user-selected refs.
managed_installed <- function(pkg, installed, recorded) {
  if (!is.null(installed) && identical(recorded$requested_ref, "default") &&
      identical(recorded$source, pkg$source) &&
      identical(recorded$remote_sha, installed$remote_sha) &&
      identical(recorded$remote_ref, installed$remote_ref)) {
    installed$remote_ref <- "default"
  }
  installed
}

usage <- function() cat("Usage: Rscript scripts/manage_r_packages.R [--component NAME] [--apply]\n",
                        "Default mode only reports; apply needs consent.r_packages=true in ~/.fiskwise/config.json.\n",
                        "R_AW_INSTALL_MISSING=false and any ancestor renv project block installs.\n", sep = "")

main <- function(args = commandArgs(trailingOnly = TRUE)) {
  if ("--help" %in% args || "-h" %in% args) return(usage())
  options <- parse_args(args)
  script_arg <- grep("^--file=", commandArgs(), value = TRUE)
  script_path <- gsub("~+~", " ", sub("^--file=", "", script_arg[[1L]]), fixed = TRUE)
  root <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
  inventory_file <- Sys.getenv("FISKWise_INVENTORY", unset = file.path(root, "packages.json"))
  registry_file <- path.expand(Sys.getenv("FISKWise_REGISTRY", unset = "~/.fiskwise/config.json"))
  if (!requireNamespace("jsonlite", quietly = TRUE)) stop("The check requires 'jsonlite' to read Fiskwise inventory and consent.", call. = FALSE)
  inventory <- jsonlite::fromJSON(inventory_file, simplifyVector = FALSE)
  registry <- if (file.exists(registry_file)) jsonlite::fromJSON(registry_file, simplifyVector = FALSE) else list()
  if (!is.null(options$component) && !options$component %in% vapply(inventory, `[[`, "", "name")) stop("Unknown component: ", options$component, call. = FALSE)

  if (options$apply && identical(tolower(Sys.getenv("R_AW_INSTALL_MISSING", unset = "")), "false")) stop("R_AW_INSTALL_MISSING=false blocks package installation.", call. = FALSE)
  if (options$apply && !isTRUE(registry$consent$r_packages)) stop("Package installation requires consent.r_packages=true in ", registry_file, call. = FALSE)
  if (options$apply && renv_project()) stop("This is inside an renv project; use renv::restore() after reviewing renv.lock.", call. = FALSE)
  user_lib <- existing_user_library()
  if (options$apply && !nzchar(user_lib)) stop("No writable existing user R library was found; no directory was created.", call. = FALSE)

  packages <- managed_packages(inventory, registry, options$component)
  pins <- names(registry$r_package_pins %||% list())
  if (options$apply && length(pins)) stop("Explicit package pins require manual dependency review; automatic updates were not applied.", call. = FALSE)
  if (length(intersect(names(packages), pins))) {
    cat("Explicit package pins preserved: ", paste(intersect(names(packages), pins), collapse = ", "), "\n", sep = "")
    packages <- packages[setdiff(names(packages), pins)]
  }
  if (!length(packages)) return(cat("No managed R packages declared for selected components.\n"))
  repos <- cran_repo_options()
  cran_index <- tryCatch(utils::available.packages(repos = repos), error = function(e) matrix(character(), nrow = 0L, ncol = 0L))
  sha_lookup <- memoize_github_sha()
  dependency_result <- expand_github_packages(packages, cran_index, sha_lookup = sha_lookup)
  packages <- dependency_result$packages
  packages <- expand_cran_packages(packages, cran_index)
  packages <- packages[setdiff(names(packages), pins)]
  if (length(dependency_result$unknown)) {
    cat("Runtime dependencies unknown; automatic changes are blocked for safety:\n  ",
        paste(dependency_result$unknown, collapse = "\n  "), "\n", sep = "")
  }
  if (options$apply) .libPaths(c(user_lib, .libPaths()))
  apply_allowed <- installation_permitted(options$apply, registry$consent$r_packages,
                                          Sys.getenv("R_AW_INSTALL_MISSING", unset = ""),
                                          renv_project(), user_lib, !length(dependency_result$unknown))
  if (options$apply && length(dependency_result$unknown)) {
    cat("Package changes skipped because required runtime dependency metadata could not be verified.\n")
  }

  preserved <- character()
  for (pkg in packages) {
    name <- pkg$name
    installed <- managed_installed(pkg, installed_package(name), registry$r_packages[[name]])
    status <- package_status(pkg, installed, cran_index, sha_lookup = sha_lookup)
    if (identical(status$state, "custom pin preserved") || identical(status$state, "missing; no ref selected")) {
      preserved <- c(preserved, name)
      cat(sprintf("%-24s %s\n", name, status$state))
      next
    }
    if (identical(status$source, "CRAN")) {
      latest <- status$latest
      cat(sprintf("%-24s %-28s installed=%s latest=%s\n", name, status$state,
                  if (is.null(installed)) "-" else installed$version,
                  if (is.na(latest)) "unknown" else latest))
      if (apply_allowed && !is.na(latest) && status$state %in% c("missing", "outdated")) {
        utils::install.packages(name, lib = user_lib, repos = repos,
                                dependencies = c("Depends", "Imports", "LinkingTo"))
      }
    } else {
      latest_sha <- status$latest_sha
      cat(sprintf("%-24s %-28s installed_sha=%s latest_sha=%s\n", name, status$state,
                  if (is.null(installed) || is.na(installed$remote_sha)) "unknown" else installed$remote_sha,
                  if (is.na(latest_sha)) "unknown" else latest_sha))
      if (apply_allowed && !is.na(latest_sha) && (is.null(installed) || !isTRUE(status$same))) {
        if (!requireNamespace("remotes", quietly = TRUE)) {
          utils::install.packages("remotes", lib = user_lib, repos = repos,
                                  dependencies = c("Depends", "Imports", "LinkingTo"))
        }
        repo <- paste0(pkg$source, "@", latest_sha)
        install_args <- list(repo = repo, lib = user_lib,
                             dependencies = c("Depends", "Imports", "LinkingTo"), upgrade = "never")
        if (!is.null(pkg$subdir)) install_args$subdir <- pkg$subdir
        do.call(remotes::install_github, install_args)
        verified <- installed_package(name)
        if (is.null(verified) || !identical(tolower(verified$remote_sha), tolower(latest_sha))) {
          stop("Installed revision could not be verified for ", name, call. = FALSE)
        }
      }
    }
  }
  if (apply_allowed) {
    registry$r_packages <- registry$r_packages %||% list()
    for (pkg in packages) {
      if (pkg$name %in% preserved) next
      installed <- installed_package(pkg$name)
      if (is.null(installed)) next
      registry$r_packages[[pkg$name]] <- c(installed, list(source = pkg$source, requested_ref = pkg$ref %||% "default",
        checked_at = format(Sys.time(), tz = "UTC", usetz = TRUE)))
    }
    temporary <- paste0(registry_file, ".packages.tmp")
    jsonlite::write_json(registry, temporary, auto_unbox = TRUE, pretty = TRUE, null = "null")
    if (!file.rename(temporary, registry_file)) stop("Could not save package report to registry.", call. = FALSE)
    if (.Platform$OS.type != "windows") Sys.chmod(registry_file, mode = "0600")
  }
}

if (sys.nframe() == 0L) main()
