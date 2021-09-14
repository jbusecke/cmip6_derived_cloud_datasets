from distributed import Client
import coiled

# Load the flow from the module
from test import flow

# # Parse command line parameters
import click

def spin_up_cluster(n_workers):
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
        software=env_name, n_workers=n_workers,
        backend_options={"region": "us-west-2"},
        shutdown_on_close=True,
    )
    client = Client(cluster)
    print("Cluster Name:", cluster.name)
    print("Dashboard:", client.dashboard_link)
    print('\n\n\n----------------------------')
    return client, cluster

@click.command()
@click.option('--source_id', default='CanESM5', help='source_id')
@click.option('--n_workers', default=6, help='Number of workers to spin up')
def wrapper(source_id, n_workers):
    flow.run(source_id=source_id)
    
    client, cluster = spin_up_cluster(n_workers)
    
    coiled.delete_cluster(name=cluster.name)
    client.close()



    
    
if __name__ == '__main__':
    wrapper()