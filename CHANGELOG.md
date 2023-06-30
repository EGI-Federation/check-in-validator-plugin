# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.2] - 2023-06-30

### Changed

- Disable logging to dedicated file

## [v0.3.1] - 2023-05-23

### Added

- Add GitHub Action for building RPM packages

## [v0.3.0] - 2023-05-16

### Added

- Add `Makefile`
- Add support for logging to syslog and/or dedicated file
- Add config for logrotate

### Changed

- Update the default paths for the config files

## [v0.2.2] - 2023-05-04

### Fixed

- Add shebang line

## [v0.2.1] - 2023-05-04

### Fixed

- Only the username of the user must be printed to stdout

## [v0.2.0] - 2023-04-25

### Added

- Add configuration file for the plugin
- Parse `iss` and `aud` claim from JWT/environment variables
- Print the mapping of the use as output

### Fixed

- Plugin exits properly, instead of printing 0/1

## [v0.1.0] - 2023-04-12

### Added

- Initial version of `egi-check-in-validator-plugin`
