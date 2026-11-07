# SPDX-License-Identifier: GPL-3.0-or-later
# Included only by the standalone companion packaging project.
set(CPACK_PACKAGE_NAME "EMB-Automation")
set(CPACK_PACKAGE_VENDOR "EMB")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Desktop automation companion for an existing KiCad installation")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "EMB Automation")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_LIST_DIR}/../../LICENSE")
set(CPACK_PACKAGE_EXECUTABLES "EMB-Automation" "EMB Automation")
set(CPACK_NSIS_EXECUTABLES_DIRECTORY "bin")
set(CPACK_NSIS_MODIFY_PATH OFF)
set(CPACK_WIX_UPGRADE_GUID "D98A7F2A-5D1C-4B9F-8B53-76F2F592750A")
# Do not take over KiCad file associations or replace its installation.
include(CPack)
