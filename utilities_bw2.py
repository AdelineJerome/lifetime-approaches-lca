import bw2data as bd
import bw2calc as bc
import pandas as pd

def reset_brightway_project(project_name):
    """
    Reset a Brightway2 project by deleting it if it already exists.

    Parameters:
    - project_name (str): The name of the project to be reset.

    Raises:
    - ValueError: If the project doesn't exist.

    Note:
    This function deletes the specified project.
    If the project doesn't exist, nothing is done.

    Example:
    >>> reset_brightway_project("my_project")
    """
    try:
        bd.projects.delete_project(project_name, True)
    except ValueError:
        pass

def reset_brightway_database(db_name):
    """
    Reset a Brightway2 database by deleting it.

    Parameters:
    - db_name (str): The name of the database to be reset.

    Note:
    This function deletes the specified database. If the database doesn't exist,
    no action is taken.

    Example:
    >>> reset_brightway_database("my_database")
    """
    if db_name in bd.databases:
        del bd.databases[db_name]

def reset_activity(act_name, database):
    """
    Reset a specific activity in a Brightway2 database by deleting it.

    Parameters:
    - act_name (str): The name of the activity to be reset.
    - database: The Brightway2 database containing the activity.

    Note:
    This function searches for an activity with the specified name in the given database
    and deletes it. If multiple activities have the same name, all of them will be deleted.

    Example:
    >>> reset_activity("my_activity", my_database)
    """
    for activity in [act for act in database if act['name'] == act_name]:
        activity.delete()

def create_new_activity(act_name, unit, location, exchanges, database, biosphere_exchanges=[], amount_product=1, name_product=""):
    """
    Create a new activity in a Brightway2 database with specified attributes and exchanges.

    Parameters:
    - act_name (str): The name of the new activity.
    - unit (str): The unit of the production from the new activity.
    - location (str): The location of the new activity.
    - exchanges (list): List of tuples containing inputs and amounts for technosphere exchanges.
    - database: The Brightway2 database in which the new activity will be created.
    - biosphere_exchanges (list, optional): List of tuples containing inputs and amounts for biosphere exchanges (default is empty).
    - amount_product (float, optional): The amount of the produced product (default is 1).
    - name_product (str, optional): The name of the produced product (default is the same as act_name).

    Note:
    This function creates a new activity in the specified Brightway2 database. It first resets
    any existing activity with the same name. The new activity includes technosphere exchanges,
    and optionally, biosphere exchanges and a production exchange.

    Example:
    >>> create_new_activity("steel production", "kilogram", "RER", [(activity1, 0.5), (activity2, 1.0)], my_database)
    """
    reset_activity(act_name, database)
    act_new = database.new_activity(
        name = act_name,
        code = act_name,
        unit = unit,
        location = location
    )
    act_new.save()
    for input, amount in exchanges:
        act_new.new_exchange(
            input = input,
            amount = amount,
            type = "technosphere"
        ).save()
    if len(biosphere_exchanges) > 0:
        for input, amount in biosphere_exchanges:
            act_new.new_exchange(
                input = input,
                amount = amount,
                type = "biosphere"
            ).save()
    act_new.save()
    
    if len(name_product) == 0:
        name_product = act_name
    act_new.new_exchange(
        input = act_new,
        amount = amount_product,
        type = "production"
    ).save()
    act_new.save()
    act_new["reference product"] = name_product
    act_new["production amount"] = amount_product
    act_new.save()

def lca_results(fu, list_methods):
    """
    Do LCIA calculations for a given functional unit (fu) using multiple impact assessment methods (list_methods).

    This function calculates the environmental impact scores for the given functional unit (fu) using the specified
    list of impact assessment methods. It iterates over each method, conducts the LCA, and aggregates the results into
    a pandas DataFrame containing the scores, units, and corresponding methods.

    Parameters:
    fu (str): The functional unit for which the LCA is performed.
    list_methods (list of methods): A list of impact assessment methods to be used for the LCA.

    Returns:
    A DataFrame containing the calculated environmental impact scores, their respective units, and the
        corresponding impact assessment methods.
    """
    list_units = [bd.methods.get(method)["unit"] for method in list_methods]
    lca = bc.LCA(demand=fu, method=list_methods[0])
    lca.lci()
    lca.lcia()
    list_scores = [lca.score]
    for method in list_methods[1:]:
        lca.switch_method(method)
        lca.lcia()
        list_scores.append(lca.score)
    return pd.DataFrame({"score": list_scores, "unit": list_units, "method": list_methods})