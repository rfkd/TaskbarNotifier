# Changelog
All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Security
- Update GitPython to version 3.1.37

## [1.0.2] - 2022-05-09
### Fixed
- Fix crash when adding a listed open app
- Fix taskbar icon of notification

## [1.0.1] - 2022-05-03
### Fixed
- Settings were not saved when auto-started due to wrong working directory

## [1.0.0] - 2022-05-01
### Added
- Add setting to auto-start Taskbar Notifier
- Allow changing the notification location
- Allow closing the notification with any mouse event
- Add setting to flash the screen shortly on notifications

## [0.3.0] - 2020-12-08
### Changed
- Replace Windows toast notifications with custom ones

## [0.2.1] - 2020-01-18
### Security
- Update PyInstaller to version 3.6 due to [CVE-2019-16784](https://github.com/advisories/GHSA-7fcj-pq9j-wh2r)

## [0.2.0] - 2019-09-15
### Added
- Add enable/disable control to tray icon context menu.

### Changed
- Allow Taskbar Notifier to run on systems without an installed Git client

## [0.1.0] - 2018-12-08
First release

[Unreleased]: https://github.com/rfkd/TaskbarNotifier/compare/1.0.2...HEAD
[1.0.2]: https://github.com/rfkd/TaskbarNotifier/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/rfkd/TaskbarNotifier/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/rfkd/TaskbarNotifier/compare/0.3.0...1.0.0
[0.3.0]: https://github.com/rfkd/TaskbarNotifier/compare/0.2.1...0.3.0
[0.2.1]: https://github.com/rfkd/TaskbarNotifier/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/rfkd/TaskbarNotifier/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/rfkd/TaskbarNotifier/releases/tag/0.1.0
