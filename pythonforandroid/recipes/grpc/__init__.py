from os.path import join
import sh
from pythonforandroid.recipe import NDKRecipe
from pythonforandroid.toolchain import (
    current_directory,
    shprint,
)
from multiprocessing import cpu_count


class GRPCRecipe(NDKRecipe):
    name = 'protobuf_cpp'
    version = 'v1.20.1'
    url = 'https://github.com/grpc/grpc/archive/{version}.zip'
    generated_libraries = [
        'libaddress_sorting.a',
        'libbenchmark.a',
        'libbenchmark_main.a',
        'libcares.so',
        'libcrypto.a',
        'libgflags.a',
        'libgflags_nothreads.a',
        'libglog.a',
        'libgpr.a',
        'libgrpc.a',
        'libgrpc++.a',
        'libgrpc_cronet.a',
        'libgrpc++_cronet.a',
        'libgrpc_csharp_ext.so',
        'libgrpc_plugin_support.a',
        'libgrpc_unsecure.a',
        'libgrpc++_unsecure.a',
        'libprotobuf.a',
        'libprotobuf-lite.a',
        'libprotoc.a',
        'libssl.a',
        'libz.a',
        'libz.so'
    ]

    def get_lib_dir(self, arch):
        return join(self.get_build_dir(arch.arch), 'build', 'lib', arch.arch)

    def get_recipe_env(self, arch):
        env = super(GRPCRecipe, self).get_recipe_env(arch)
        env['ANDROID_NDK'] = self.ctx.ndk_dir
        env['ANDROID_SDK'] = self.ctx.sdk_dir
        return env

    def build_arch(self, arch):
        build_dir = join(self.get_build_dir(arch.arch), 'build')
        shprint(sh.mkdir, '-p', build_dir)
        with current_directory(build_dir):
            env = self.get_recipe_env(arch)

            python_major = self.ctx.python_recipe.version[0]
            python_include_root = self.ctx.python_recipe.include_root(arch.arch)
            python_site_packages = self.ctx.get_site_packages_dir()
            python_link_root = self.ctx.python_recipe.link_root(arch.arch)
            python_link_version = self.ctx.python_recipe.major_minor_version_string
            if 'python3' in self.ctx.python_recipe.name:
                python_link_version += 'm'
            python_library = join(python_link_root,
                                  'libpython{}.so'.format(python_link_version))
            python_include_numpy = join(python_site_packages,
                                        'numpy', 'core', 'include')

            shprint(sh.cmake,
                    '-DP4A=ON',
                    '-DANDROID_ABI={}'.format(arch.arch),
                    '-DANDROID_STANDALONE_TOOLCHAIN={}'.format(self.ctx.ndk_dir),
                    '-DANDROID_NATIVE_API_LEVEL={}'.format(self.ctx.ndk_api),
                    '-DANDROID_EXECUTABLE={}/tools/android'.format(env['ANDROID_SDK']),

                    '-DCMAKE_TOOLCHAIN_FILE={}'.format(
                        join(self.ctx.ndk_dir, 'build', 'cmake',
                             'android.toolchain.cmake')),
                    # Make the linkage with our python library, otherwise we
                    # will get dlopen error when trying to import cv2's module.
                    '-DCMAKE_SHARED_LINKER_FLAGS=-L{path} -lpython{version}'.format(
                        path=python_link_root,
                        version=python_link_version),

                    '-DBUILD_WITH_STANDALONE_TOOLCHAIN=ON',
                    # Force to build as shared libraries the cv2's dependant
                    # libs or we will not be able to link with our python
                    '-DBUILD_SHARED_LIBS=ON',
                    '-DBUILD_STATIC_LIBS=OFF',
                    '-Dprotobuf_BUILD_PROTOC_BINARIES=OFF',
                    '-DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}"',
                    '-DCMAKE_FIND_ROOT_PATH="${INSTALL_DIR}"',
                    '-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=BOTH',
                    '-DCMAKE_EXE_LINKER_FLAGS="-llog"',
                    '-DProtobuf_PROTOC_EXECUTABLE=/usr/local/bin/protoc',
                    '-DHAVE_THREAD_SAFETY_ATTRIBUTES=ON',
                    '-DHAVE_GNU_POSIX_REGEX=ON',
                    '-DHAVE_STD_REGEX=ON',
                    '-DRUN_HAVE_STD_REGEX=ON',
                    '-DHAVE_POSIX_REGEX=1',
                    '-DRUN_HAVE_POSIX_REGEX=ON',
                    '-DHAVE_STEADY_CLOCK=ON',
                    '-DgRPC_INSTALL=ON',
                    '-DgRPC_BUILD_TESTS=OFF',
                    '-DgRPC_PROTOBUF_PROVIDER=package',
                    '-DgRPC_ZLIB_PROVIDER=package',
                    '-DgRPC_CARES_PROVIDER=package',
                    '-DgRPC_SSL_PROVIDER=package',
                    '-DgRPC_GFLAGS_PROVIDER=package',
                    '-DgRPC_BUILD_CODEGEN=OFF',


                    # Define python's paths for: exe, lib, includes, numpy...
                    '-DPYTHON_DEFAULT_EXECUTABLE={}'.format(self.ctx.hostpython),
                    '-DPYTHON{major}_EXECUTABLE={host_python}'.format(
                        major=python_major, host_python=self.ctx.hostpython),
                    '-DPYTHON{major}_INCLUDE_PATH={include_path}'.format(
                        major=python_major, include_path=python_include_root),
                    '-DPYTHON{major}_LIBRARIES={python_lib}'.format(
                        major=python_major, python_lib=python_library),
                    '-DPYTHON{major}_NUMPY_INCLUDE_DIRS={numpy_include}'.format(
                        major=python_major, numpy_include=python_include_numpy),
                    '-DPYTHON{major}_PACKAGES_PATH={site_packages}'.format(
                        major=python_major, site_packages=python_site_packages),

                    self.get_build_dir(arch.arch),
                    _env=env)
            shprint(sh.make, '-j' + str(cpu_count()))
            # Copy third party shared libs that we need in our final apk
            sh.cp('-a', sh.glob('./lib/{}/lib*.a'.format(arch.arch)),
                  self.ctx.get_libs_dir(arch.arch))


recipe = GRPCRecipe()
