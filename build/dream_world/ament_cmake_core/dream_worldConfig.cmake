# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_dream_world_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED dream_world_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(dream_world_FOUND FALSE)
  elseif(NOT dream_world_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(dream_world_FOUND FALSE)
  endif()
  return()
endif()
set(_dream_world_CONFIG_INCLUDED TRUE)

# output package information
if(NOT dream_world_FIND_QUIETLY)
  message(STATUS "Found dream_world: 0.0.0 (${dream_world_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'dream_world' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${dream_world_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(dream_world_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${dream_world_DIR}/${_extra}")
endforeach()
