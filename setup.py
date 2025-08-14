from setuptools import setup, find_packages

setup(
    name="wazo-call-distributor",
    version="0.1.0",
    description="Minimal call distribution + survey transfer for wazo-calld",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["wazo-calld-client>=2.0.0", "Flask>=2.0.0"],
    entry_points={
        # This is how wazo-calld discovers stack plugins
        "wazo_calld.plugins": [
            "call_distributor = wazo_call_distributor.plugin:Plugin",
        ],
    },
)
