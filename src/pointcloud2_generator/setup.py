from setuptools import find_packages, setup

package_name = 'pointcloud2_generator'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/pointcloud2_generator']),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/generator_launch.py']),
        ('share/' + package_name + '/config', ['config/scene.yaml', 'config/params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ralf',
    maintainer_email='ralf@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
             'generator = pointcloud2_generator.generator_node:main',
        ],
    },
)
