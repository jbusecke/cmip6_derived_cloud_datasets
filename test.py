from prefect import task, Flow, Parameter, unmapped
from prefect.executors import DaskExecutor
from prefect.tasks.prefect import StartFlowRun
import intake
import fsspec
from cmip6_preprocessing.preprocessing import combined_preprocessing
from cmip6_preprocessing.utils import cmip6_dataset_id

@task
def discovery_and_preprocess(**search_kwargs):
    col = intake.open_esm_datastore("https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.json")
    cat = col.search(**search_kwargs)
    ddict = cat.to_dataset_dict(
        zarr_kwargs={
            'consolidated':True,
            'use_cftime':True,
        },
        storage_options={'anon':True},
        preprocess = combined_preprocessing,
        aggregate = False,
    )
    
    # This could contain some custom combination code
    # for now just reduce the number of datasets
    ddict_pp = {k:ddict[k] for k in list(ddict.keys())[0:3]}
    
    
    return list(ddict_pp.values()) # need to return a list to map over....not ideal beause the resulting tasks are not labelled
    

@task
def naive_mean(ds):
    out = ds.mean(['lev','y', 'x'], keep_attrs=True)
    return out

@task
def clean_ds_attrs(ds):
    """Needed to save to zarr"""
    for attr in ['intake_esm_varname']:
        if attr in ds.attrs:
            del ds.attrs[attr]
    return ds

@task
def store_zarr(ds, ofolder):
    # for testing just average the first 12 steps
    ds = ds.isel(time=slice(0,240))
#     filename = 'short_'+ cmip6_dataset_id(ds) +'.zarr'

#     mapper = fsspec.get_mapper(ofolder+'/'+filename)
#     print(f"Saving to {str(mapper)}")
#     ds.to_zarr(mapper, mode='w')
#     return str(mapper)

    # drop in replacement (just load for now, not save)
    ds = ds.load()
    print(ds)
    return ds

    
    
with Flow("Test-Mean-CMIP6") as flow:
    ofolder = Parameter("ofolder", default=None)
    source_id = Parameter("source_id", default="CanESM5")
    variable_id = Parameter("variable_id", default="thetao")
    experiment_id = Parameter("experiment_id", default="historical")
    grid_label = Parameter("grid_label", default='gn')
    table_id = Parameter("table_id", default='Omon')
    
    datasets = discovery_and_preprocess(
        source_id=source_id,
        variable_id=variable_id,
        experiment_id=experiment_id,
        grid_label=grid_label,
        table_id = table_id
    )
    
    mapped_means = naive_mean.map(ds=datasets)
    mapped_mean_clean = clean_ds_attrs.map(ds=mapped_means)
    filepaths = store_zarr.map(ds=mapped_mean_clean, ofolder=unmapped(ofolder))
