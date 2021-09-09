from distributed import Client
import coiled

# Load the flow from the module
from test import flow

# set up the cluster before executing the run
env_name = "cmip6_derived_cloud_datasets"

## use the pangeo containerfor the software env
coiled.create_software_environment(
    name=env_name,
    conda='environment.yml', # this will take longer...but I guess thats ok for now?
    # couldnt get this to work yet
#     container='pangeo/pangeo-notebook:latest',   # matches Pangeo Cloud AWS production cluster
)

# Create a Dask cluster which uses 
# software environment
cluster = coiled.Cluster(
    software=env_name, n_workers=10,
    backend_options={"region": "us-west-2"}
)
client = Client(cluster)
print(print("Dashboard:", client.dashboard_link))
print('\n\n\n----------------------------')


flow.run()
