#
# CPack Packaging Configuration for MAH Quantum
# Devashri S Embedded System Technologies
# Powered by KiCad EDA Core
#

set( CPACK_PACKAGE_NAME "MAH-Quantum-EDA" )
set( CPACK_PACKAGE_VENDOR "Devashri S Embedded System Technologies" )
set( CPACK_PACKAGE_DESCRIPTION_SUMMARY "MAH Quantum - Autonomous Hardware Foundry (Powered by KiCad)" )
set( CPACK_PACKAGE_VERSION_MAJOR "1" )
set( CPACK_PACKAGE_VERSION_MINOR "0" )
set( CPACK_PACKAGE_VERSION_PATCH "0" )
set( CPACK_PACKAGE_INSTALL_DIRECTORY "MAH Quantum\\EDA" )
set( CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_LIST_DIR}/../LICENSE" )

# NSIS (.exe) Installer Generator Settings
set( CPACK_NSIS_DISPLAY_NAME "MAH Quantum - Autonomous Embedded Foundry" )
set( CPACK_NSIS_PACKAGE_NAME "MAH Quantum" )
set( CPACK_NSIS_HELP_LINK "https://www.mahquantum.com" )
set( CPACK_NSIS_URL_INFO_ABOUT "https://www.mahquantum.com" )
set( CPACK_NSIS_MODIFY_PATH ON )
set( CPACK_NSIS_ENABLE_UNINSTALL_BEFORE_INSTALL ON )

# File Associations in Windows Explorer
set( CPACK_NSIS_EXTRA_INSTALL_COMMANDS "
  WriteRegStr HKCR '.kicad_sch' '' 'MAHQuantum.Schematic'
  WriteRegStr HKCR 'MAHQuantum.Schematic\\\\shell\\\\open\\\\command' '' '\\\"$INSTDIR\\\\bin\\\\kicad.exe\\\" \\\"%1\\\"'
  WriteRegStr HKCR '.kicad_pcb' '' 'MAHQuantum.PCB'
  WriteRegStr HKCR 'MAHQuantum.PCB\\\\shell\\\\open\\\\command' '' '\\\"$INSTDIR\\\\bin\\\\kicad.exe\\\" \\\"%1\\\"'
  WriteRegStr HKCR '.kicad_pro' '' 'MAHQuantum.Project'
  WriteRegStr HKCR 'MAHQuantum.Project\\\\shell\\\\open\\\\command' '' '\\\"$INSTDIR\\\\bin\\\\kicad.exe\\\" \\\"%1\\\"'
" )

# WiX (.msi) Enterprise Installer Settings
set( CPACK_WIX_UPGRADE_GUID "D98A7F2A-5D1C-4B9F-8B53-76F2F592750A" )
set( CPACK_WIX_PRODUCT_GUID "B41A3E2F-1D8C-4C7E-9F41-18F1C37B9210" )
set( CPACK_WIX_PROPERTY_ARPCOMMENTS "Devashri S Embedded System Technologies - MAH Quantum Autonomous Hardware Platform (Powered by KiCad Core)" )

# Define Generators
set( CPACK_GENERATOR "NSIS;WIX" )
include( CPack )
