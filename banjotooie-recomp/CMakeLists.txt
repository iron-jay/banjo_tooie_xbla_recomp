# banjotooie - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(banjotooie LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

# Sources
set(BANJOTOOIE_SOURCES
    src/main.cpp
)

if(WIN32)
    # banjotooie.rc embeds MAINICON (the exe + window-class icon) into the exe.
    enable_language(RC)
    add_executable(banjotooie WIN32 ${BANJOTOOIE_SOURCES}
        ${CMAKE_CURRENT_SOURCE_DIR}/banjotooie.rc)
else()
    add_executable(banjotooie ${BANJOTOOIE_SOURCES})
endif()

rexglue_setup_target(banjotooie)

# --- Local build fix -------------------------------------------------------
# The SDK harness rex_app.cpp (injected into this target by
# rexglue_configure_target) includes imgui.h, but imgui's include dir isn't
# propagated through rex::runtime in the REXSDK_DIR (source-tree) build path.
# Scope the include to just these harness sources so the 48 generated TUs
# aren't invalidated / rebuilt.
set_source_files_properties(
    "${REXSDK_DIR}/src/ui/rex_app.cpp"
    "${REXSDK_DIR}/src/ui/windowed_app_main_win.cpp"
    PROPERTIES INCLUDE_DIRECTORIES
        "${REXSDK_DIR}/thirdparty/imgui;${REXSDK_DIR}/src;${CMAKE_BINARY_DIR}/rexglue-sdk/include"
)
