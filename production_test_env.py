from distributed import Client
import coiled

# Load the flow from the module
from test import flow

# # Parse command line parameters
import click

@click.command()
@click.option('--source_id', default='CanESM5', help='source_id')
def run_flow(source_id):
    flow.run(source_id=source_id)
    
    
if __name__ == '__main__':
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
        software=env_name, n_workers=6,
        backend_options={"region": "us-west-2"},
        shutdown_on_close=True,
    )
    client = Client(cluster)
    print("Cluster Name:", cluster.name)
    print("Dashboard:", client.dashboard_link)
    print('\n\n\n----------------------------')


    run_flow()
    
    coiled.delete_cluster(name=cluster.name)
    client.close()
