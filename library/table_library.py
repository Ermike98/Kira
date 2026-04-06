import pandas as pd

from kira.kdata.ktable import KTable, K_TABLE_TYPE
from kira.kdata.karray import KArray, K_ARRAY_STRING_TYPE, K_ARRAY_TYPE
from kira.kdata.kliteral import KLiteral, KLiteralType, K_INTEGER_TYPE, K_STRING_TYPE
from kira.knodes.kfunction import kfunction
from kira.ktypeinfo.union_type import KUnionTypeInfo
from kira.kdata.kerrorvalue import KErrorValue
from kira.kexpections.kgenericexception import KGenericException
from library.builtin_library import k_builtin_library

# Table Functions

# nrows(df) -> int # number of rows
@kfunction(
    inputs=[("df", K_TABLE_TYPE)],
    outputs=[("n", K_INTEGER_TYPE)],
    name="nrows",
    use_values=True,
    use_context=False
)
def k_table_nrows(df_obj: KTable):
    return [KLiteral(len(df_obj.value), K_INTEGER_TYPE)]

k_builtin_library.register(k_table_nrows)

# ncols(df) -> int # number of columns
@kfunction(
    inputs=[("df", K_TABLE_TYPE)],
    outputs=[("n", K_INTEGER_TYPE)],
    name="ncols",
    use_values=True,
    use_context=False
)
def k_table_ncols(df_obj: KTable):
    return [KLiteral(len(df_obj.value.columns), K_INTEGER_TYPE)]

k_builtin_library.register(k_table_ncols)

# columns(df) -> array[str] # column names
@kfunction(
    inputs=[("df", K_TABLE_TYPE)],
    outputs=[("cols", K_ARRAY_STRING_TYPE)],
    name="columns",
    use_values=True,
    use_context=False
)
def k_table_columns(df_obj: KTable):
    return [KArray(pd.Series(list(df_obj.value.columns)), KLiteralType.STRING)]

k_builtin_library.register(k_table_columns)


# slice(df, rows: array[int], columns: array[str]) -> table # DO NOT IMPLEMENT
# filter_columns(df, columns: array[str]) -> table # DO NOT IMPLEMENT

# select(df, columns: array[str]) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("columns", K_ARRAY_STRING_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="select",
    use_values=True,
    use_context=False
)
def k_table_select(df_obj: KTable, columns_obj: KArray):
    cols = columns_obj.value.tolist()
    return [KTable(df_obj.value[cols])]

k_builtin_library.register(k_table_select)

# head(df, n=5) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("n", K_INTEGER_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="head",
    use_values=True,
    use_context=False,
    default_inputs={"n": KLiteral(5, K_INTEGER_TYPE)}
)
def k_table_head(df_obj: KTable, n_obj: KLiteral):
    return [KTable(df_obj.value.head(n_obj.value))]

k_builtin_library.register(k_table_head)

# tail(df, n=5) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("n", K_INTEGER_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="tail",
    use_values=True,
    use_context=False,
    default_inputs={"n": KLiteral(5, K_INTEGER_TYPE)}
)
def k_table_tail(df_obj: KTable, n_obj: KLiteral):
    return [KTable(df_obj.value.tail(n_obj.value))]

k_builtin_library.register(k_table_tail)

# add_column(df, name: string, values: array) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("name", K_STRING_TYPE), ("values", K_ARRAY_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="add_column",
    use_values=True,
    use_context=False
)
def k_table_add_column(df_obj: KTable, name_obj: KLiteral, values_obj: KArray):
    new_df = df_obj.value.copy()
    new_df[name_obj.value] = values_obj.value
    return [KTable(new_df)]

k_builtin_library.register(k_table_add_column)

# remove_column(df, name: string) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("name", K_STRING_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="remove_column",
    use_values=True,
    use_context=False
)
def k_table_remove_column(df_obj: KTable, name_obj: KLiteral):
    new_df = df_obj.value
    if name_obj.value in new_df.columns:
        new_df = new_df.drop(columns=[name_obj.value])
    return [KTable(new_df)]

# remove_columns(df, names: array[string]) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("names", K_ARRAY_STRING_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="remove_columns",
    use_values=True,
    use_context=False
)
def k_table_remove_columns(df_obj: KTable, names_obj: KArray):
    new_df = df_obj.value
    # TODO: Add error handling for when column names do not exist
    cols = [name for name in names_obj.value.to_list() if name in new_df.columns]
    if cols:
        new_df = new_df.drop(columns=cols)
    return [KTable(new_df)]

k_builtin_library.register(k_table_remove_columns)

# rename_column(df, old_name: string, new_name: string) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("old_name", K_STRING_TYPE), ("new_name", K_STRING_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="rename_column",
    use_values=True,
    use_context=False
)
def k_table_rename_column(df_obj: KTable, old_name_obj: KLiteral, new_name_obj: KLiteral):
    new_df = df_obj.value.rename(columns={old_name_obj.value: new_name_obj.value})
    return [KTable(new_df)]

k_builtin_library.register(k_table_rename_column)

# update_column(df, name: string, values: array) -> table # Do NOT IMPLEMENT - Implement via workflow

# transpose(df) -> table
@kfunction(
    inputs=[("df", K_TABLE_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="transpose",
    use_values=True,
    use_context=False
)
def k_table_transpose(df_obj: KTable):
    return [KTable(df_obj.value.T)]

k_builtin_library.register(k_table_transpose)

# pivot(df: table, index: str | array[str], columns: str | array[str], value: str) -> table
@kfunction(
    inputs=[
        ("df", K_TABLE_TYPE),
        ("index", KUnionTypeInfo([K_STRING_TYPE, K_ARRAY_STRING_TYPE])),
        ("columns", KUnionTypeInfo([K_STRING_TYPE, K_ARRAY_STRING_TYPE])),
        ("value", K_STRING_TYPE)
    ],
    outputs=[("y", K_TABLE_TYPE)],
    name="pivot",
    use_values=True,
    use_context=False
)
def k_table_pivot(df_obj: KTable, index_obj, columns_obj, value_obj: KLiteral):
    idx = index_obj.value.tolist() if isinstance(index_obj, KArray) else index_obj.value
    cols = columns_obj.value.tolist() if isinstance(columns_obj, KArray) else columns_obj.value
    pivoted = df_obj.value.pivot(index=idx, columns=cols, values=value_obj.value)
    return [KTable(pivoted.reset_index())]

k_builtin_library.register(k_table_pivot)

# melt(df: table, id_vars: str | array[str]) -> table
@kfunction(
    inputs=[
        ("df", K_TABLE_TYPE),
        ("id_vars", KUnionTypeInfo([K_STRING_TYPE, K_ARRAY_STRING_TYPE]))
    ],
    outputs=[("y", K_TABLE_TYPE)],
    name="melt",
    use_values=True,
    use_context=False
)
def k_table_melt(df_obj: KTable, id_vars_obj):
    idx = id_vars_obj.value.tolist() if isinstance(id_vars_obj, KArray) else id_vars_obj.value
    return [KTable(df_obj.value.melt(id_vars=idx))]

k_builtin_library.register(k_table_melt)

# aggregate(df: table, by: str | array[str], columns: str | array[str], functions: str | array[str]) -> table # DO NOT IMPLEMENT

# join(df1: table, df2: table, on: str | array[str], how: str = "inner") -> table
@kfunction(
    inputs=[
        ("df1", K_TABLE_TYPE),
        ("df2", K_TABLE_TYPE),
        ("on", KUnionTypeInfo([K_STRING_TYPE, K_ARRAY_STRING_TYPE])),
        ("how", K_STRING_TYPE)
    ],
    outputs=[("y", K_TABLE_TYPE)],
    name="join",
    use_values=False,
    use_context=False,
    default_inputs={"how": KLiteral("inner", K_STRING_TYPE)}
)
def k_table_join(df1_data, df2_data, on_data, how_data):
    df1_obj = df1_data.value
    df2_obj = df2_data.value
    on_obj = on_data.value
    how_obj = how_data.value
    
    on_cols = on_obj.value.tolist() if isinstance(on_obj, KArray) else on_obj.value
    suffixes = (f"_{df1_data.name}", f"_{df2_data.name}")
    
    joined = pd.merge(df1_obj.value, df2_obj.value, on=on_cols, how=how_obj.value, suffixes=suffixes)
    return [KTable(joined)]

k_builtin_library.register(k_table_join)

# hstack(df1: table, df2: table) -> table
@kfunction(
    inputs=[("df1", K_TABLE_TYPE), ("df2", K_TABLE_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="hstack",
    use_values=True,
    use_context=False
)
def k_table_hstack(df1_obj: KTable, df2_obj: KTable):
    return [KTable(pd.concat([df1_obj.value, df2_obj.value], axis=1))]

k_builtin_library.register(k_table_hstack)

# vstack(df1: table, df2: table) -> table
@kfunction(
    inputs=[("df1", K_TABLE_TYPE), ("df2", K_TABLE_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="vstack",
    use_values=True,
    use_context=False
)
def k_table_vstack(df1_obj: KTable, df2_obj: KTable):
    return [KTable(pd.concat([df1_obj.value, df2_obj.value], axis=0, ignore_index=True))]

k_builtin_library.register(k_table_vstack)

# concat(dfs: array[table]) -> table
@kfunction(
    inputs=[("dfs", K_ARRAY_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="concat",
    use_values=True,
    use_context=False
)
def k_table_concat(dfs_obj: KArray):
    if not all(isinstance(df, KTable) for df in dfs_obj.value.to_list()):
        return [KErrorValue(KGenericException("All elements in the array must be KTable"))]
    return [KTable(pd.concat([df.value for df in dfs_obj.value.to_list()], axis=0, ignore_index=True))]

k_builtin_library.register(k_table_concat)

# rolling(df, window, columns: str | array[str], functions: str | array[str]) -> table # DO NOT IMPLEMENT

# sort_table(df, by: str | array[str], ascending: bool = True)
@kfunction(
    inputs=[("df", K_TABLE_TYPE), ("by", KUnionTypeInfo([K_STRING_TYPE, K_ARRAY_STRING_TYPE])), ("ascending", K_BOOLEAN_TYPE)],
    outputs=[("y", K_TABLE_TYPE)],
    name="sort_table",
    use_values=True,
    use_context=False,
    default_inputs={"ascending": KLiteral(True, K_BOOLEAN_TYPE)}
)
def k_table_sort_table(df_obj: KTable, by_obj, ascending_obj: KLiteral):
    by_cols = by_obj.value.tolist() if isinstance(by_obj, KArray) else by_obj.value
    return [KTable(df_obj.value.sort_values(by=by_cols, ascending=ascending_obj.value))]

k_builtin_library.register(k_table_sort_table)

# Table and Array Functions

# getitem(x,  ) # get value for specific index

# filter(x: table | array, condition: array[bool]) -> table | array
@kfunction(
    inputs=[("x", KUnionTypeInfo([K_TABLE_TYPE, K_ARRAY_TYPE])), ("condition", K_ARRAY_BOOLEAN_TYPE)],
    outputs=[("y", KUnionTypeInfo([K_TABLE_TYPE, K_ARRAY_TYPE]))],
    name="filter",
    use_values=True,
    use_context=False
)
def k_table_filter(x_obj, condition_obj):
    if isinstance(x_obj, KTable):
        return [KTable(x_obj.value[condition_obj.value])]
    return [KArray(x_obj.value[condition_obj.value])]

k_builtin_library.register(k_table_filter)


# String Functions - both string literals and arrays

# string(x: any) -> string # convert to string

# trim(x: string | array[string]) -> string | array[string] # remove whitespaces
# upper(x: string | array[string]) -> string | array[string]
# lower(x: string | array[string]) -> string | array[string]
# proper(x: string | array[string]) -> string | array[string] # capitalize first letter

# text_len(x: string | array[string]) -> string | array[string]

# text_replace(x: string | array[string], old: string, new: string) -> string | array[string]

# text_split(x: string | array[string], delimiter: string) -> string | array[string]
# text_join(x: array[string] | array[array[string]]) -> string | array[string]

# text_find(x: string | array[string], needle: string) -> int | array[int]
# text_contains(x: string | array[string], needle: string) -> boolean | array[boolean]

# text_slice(x: string | array[string], start: int, stop: int) -> string | array[string] # slice string
# text_before(x: string | array[string], delimiter: string) -> string | array[string]
# text_after(x: string | array[string], delimiter: string) -> string | array[string]
# text_between(x: string | array[string], left_delimiter: string, right_delimiter: string) -> string | array[string]

# DateTime Functions

# date(x: string | array[string]) -> date | array[date]
# datetime(x: string | array[string]) -> datetime | array[datetime]

# today()
# now()

# DateDiff as DataType
# convertion function from DateDiff to periods, e.g. days, months, years, working days, quarters, hour, minutes, seconds, etc

