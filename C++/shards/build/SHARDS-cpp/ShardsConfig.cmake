
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was ShardsConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

set_and_check(shards_INCLUDE_DIR "${PACKAGE_PREFIX_DIR}/include")
set_and_check(shards_CMAKE_DIR "${PACKAGE_PREFIX_DIR}/lib/cmake/Shards")

if (NOT TARGET Shards::Shards)
   include("${shards_CMAKE_DIR}/ShardsTargets.cmake")
endif()

set(shards_LIBRARIES Shards)

if (NOT shards_FIND_QUIETLY)
  message(STATUS "Found Shards: ${PACKAGE_PREFIX_DIR}")
endif()
