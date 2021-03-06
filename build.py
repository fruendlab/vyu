from pybuilder.core import use_plugin, init
from pybuilder.vcs import count_travis

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "vyu"
default_task = "publish"
version = '0.' + count_travis()


@init
def set_properties(project):
    project.depends_on('imageio')
    project.depends_on('numpy')
    project.depends_on('scikit-image')
    project.depends_on('scipy')
    project.depends_on('docopt')
    
    project.set_property('coverage_break_build', False)
