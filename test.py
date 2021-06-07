import os
from prefect import task, Flow, Parameter
from prefect.executors import DaskExecutor
import intake
import fsspec
from cmip6_preprocessing.preprocessing import combined_preprocessing
from distributed import Client
import coiled


@task
def load_ddict(**search_kwargs):
    col = intake.open_esm_datastore("https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.json")
    cat = col.search(**search_kwargs)
    
    return cat.to_dataset_dict(
        zarr_kwargs={
            'consolidated':True,
            'use_cftime':True
        },
        preprocess = combined_preprocessing,
        aggregate = False,
    )

@task(nout=2)
def choose_first_dataset(ddict):
    return ddict.popitem()
    

@task
def naive_mean(ds):
    out = ds.mean(['lev','y', 'x'], keep_attrs=True)
    return out

@task
def clean_ds_attrs(ds):
    for attr in ['intake_esm_varname']:
        if attr in ds.attrs:
            del ds.attrs[attr]
    return ds

@task
def store_zarr(ds, ofolder, short, filename):
    if short:
        ds = ds.isel(time=slice(0,36))
        filename = 'short_'+ filename
        
    mapper = fsspec.get_mapper(ofolder+'/'+filename)
    print(f"Saving to {filename}")
    ds.to_zarr(mapper, mode='w')
    
PANGEO_SCRATCH = os.environ['PANGEO_SCRATCH']
scratch = f'{PANGEO_SCRATCH}/cmip6_derived'
    
with Flow("Test-Mean-CMIP6") as flow:
    source_id = Parameter("source_id", default="GFDL-CM4")
    variable_id = Parameter("variable_id", default="thetao")
    experiment_id = Parameter("experiment_id", default="historical")
    grid_label = Parameter("grid_label", default='gn')
    table_id = Parameter("table_id", default='Omon')
    short = Parameter("short", default=False)
    filename = Parameter("filename", default='just_some_test.zarr')
    
    ddict = load_ddict(
        source_id=source_id,
        variable_id=variable_id,
        experiment_id=experiment_id,
        grid_label=grid_label,
        table_id = table_id
    )
    
    # for now just use the first one
    ds_name, ds = choose_first_dataset(ddict)
    
    ds_mean = naive_mean(ds)
    
    ds_mean = clean_ds_attrs(ds_mean)
    
    store_zarr(ds_mean, scratch, short, filename)
    
    
    
if __name__=="__main__":
    
    env_name = "cmip6_derived_cloud_datasets"
    

    ## use the pangeo containerfor the software env
    coiled.create_software_environment(
        name=env_name,
        container='pangeo/pangeo-notebook:2021.02.02',   # matches Pangeo Cloud AWS production cluster
    )

    # Create a Dask cluster which uses 
    # software environment
    cluster = coiled.Cluster(software=env_name, n_workers=10)#,
    client = Client(cluster)
    print(client)
    
    coiled_executor = DaskExecutor(cluster)
    flow_state = flow.run(executor=coiled_executor, filename='script_test.nc', short=False)