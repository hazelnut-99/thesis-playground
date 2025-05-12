#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Shards::Shards" for configuration ""
set_property(TARGET Shards::Shards APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(Shards::Shards PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_NOCONFIG "CXX"
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libShards.a"
  )

list(APPEND _cmake_import_check_targets Shards::Shards )
list(APPEND _cmake_import_check_files_for_Shards::Shards "${_IMPORT_PREFIX}/lib/libShards.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
