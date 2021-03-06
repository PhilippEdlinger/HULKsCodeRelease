# Find ode
#
# This module defines
# ODE_INCLUDE_DIRS
# ODE_LIBRARIES
# ODE_FOUND

find_path(ODE_INCLUDE_DIR NAMES ode.h HINTS /usr/include $ENV{ODE_HOME}/include PATH_SUFFIXES ode)
find_library(ODE_LIBRARY NAMES ode-double HINTS /lib /usr/lib $ENV{ODE_HOME}/lib)
if(NOT ODE_LIBRARY)
  find_library(ODE_LIBRARY NAMES ode HINTS /lib /usr/lib $ENV{ODE_HOME}/lib)
endif(NOT ODE_LIBRARY)

set(ODE_INCLUDE_DIRS ${ODE_INCLUDE_DIR})
set(ODE_LIBRARIES ${ODE_LIBRARY})

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(ODE DEFAULT_MSG ODE_LIBRARY ODE_INCLUDE_DIR)

mark_as_advanced(ODE_INCLUDE_DIR ODE_LIBRARY)
