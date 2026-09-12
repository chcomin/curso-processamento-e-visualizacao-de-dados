"""Suíte de testes de integridade para o conjunto de dados diabetic_data.csv."""

from functools import partial

# Valores considerados ausentes pelo pandas
# https://pandas.pydata.org/docs/user_guide/io.html#io-navaluesconst
PANDAS_NA = ['-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A N/A', '#N/A', 'N/A', 'n/a', 'NA', 
             '<NA>', '#NA', 'NULL', 'null', 'NaN', '-NaN', 'nan', '-nan', 'None', '']

def check_column_names(df):
    """Checa a presença de espaços em branco, caracteres especiais e colisões de nomes de colunas."""

    issues = []
    seen = {}
    for col in df.columns:
        if col != col.strip():
            issues.append(f"Coluna '{col}' possui espaços em branco nas bordas")
        normalized = col.strip().lower()
        if normalized in seen:
            issues.append(f"Colunas '{col}' e '{seen[normalized]}' colidem após normalização")
        seen[normalized] = col
        if not col.strip().replace("_", "").replace("-", "").isalnum():
            issues.append(f"Coluna '{col}' contém caracteres especiais")
    return issues

def check_dtypes(df, expected_schema):
    """Compara os tipos inferidos do DataFrame com um dicionário de tipos esperados."""

    issues = []
    for column, expected_type in expected_schema.items():
        if column not in df.columns:
            issues.append(f"Coluna '{column}' ausente no DataFrame")
            continue
        actual_type = str(df[column].dtype)
        if actual_type != expected_type:
            issues.append(
                f"Coluna '{column}': esperado {expected_type}, encontrado {actual_type}"
                )
    return issues

def check_duplicate(df, key_column):
    """Checa se a coluna de chave primária possui valores duplicados e se há linhas 
    totalmente duplicadas."""

    duplicated = df[key_column][df[key_column].duplicated(keep=False)]
    issues = []
    if not duplicated.empty:
        keys = ", ".join(duplicated.unique().astype(str)[:10])
        issues.append(
            f"Chave '{key_column}' possui {duplicated.nunique()} valores "
            f"repetidos (primeiros: {keys})"
        )
    if df.duplicated().any():
        issues.append(f"Existem {int(df.duplicated().sum())} linhas totalmente duplicadas")
    return issues

def check_sentinel_values(df, sentinels):
    """Checa se há valores sentinela de ausência de dado nas colunas do DataFrame."""

    issues = []
    for col in df.columns:
        for sentinel in sentinels:
            count = int((df[col] == sentinel).sum())
            if count:
                issues.append(
                    f"Coluna '{col}' possui {count} valores '{sentinel}' "
                    f"({count / len(df):.1%} das linhas)"
                )

    return issues

def check_zero_variance(df):
    """Checa se há colunas com um único valor."""

    constant = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]
    if not constant:
        return []
    return [f"Colunas com um único valor: {', '.join(constant)}"]

def check_numeric_bounds(df, bounds):
    """Checa se os valores numéricos estão dentro de limites esperados."""

    issues = []
    for col, (minimum, maximum) in bounds.items():
        series = df[col]
        violations = (series < minimum) | (series > maximum)
        if violations.any():
            issues.append(
                f"Coluna '{col}' possui {int(violations.sum())} valores menores que {minimum}"
                f" ou maiores que {maximum} (mín={series.min()}, máx={series.max()})"
            )
    return issues

# ---
# Checagens específicas para o conjunto de dados de diabetes
# ---

def check_medication_consistency(df):
    """A coluna diabetesMed indica se foi prescrito algum medicamento para diabetes, e a coluna 
    change indica se houve alteração na medicação. Ambas devem ser consistentes com as 23 colunas
    de medicamentos do DataFrame."""

    # Colunas de medicamentos: cada uma registra o uso do fármaco no atendimento.
    drug_columns = [
        "metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
        "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
        "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide",
        "examide", "citoglipton", "insulin", "glyburide-metformin",
        "glipizide-metformin", "glimepiride-pioglitazone",
        "metformin-rosiglitazone", "metformin-pioglitazone",
    ]

    drugs = df[drug_columns]
    # Usou algum medicamento?
    uses_drug = (drugs != "No").any(axis=1)
    # A dose de algum medicamento foi alterada (Up ou Down)?
    changed_dose = drugs.isin(["Up", "Down"]).any(axis=1)

    cases = [
        ((df["diabetesMed"] == "No") & uses_drug, "diabetesMed='No' mas há fármaco prescrito"),
        ((df["diabetesMed"] == "Yes") & ~uses_drug, "diabetesMed='Yes' mas nenhum fármaco prescrito"),
        ((df["change"] == "No") & changed_dose, "change='No' mas há fármaco com dose Up/Down"),
        ((df["change"] == "Ch") & ~changed_dose, "change='Ch' mas nenhum fármaco com dose Up/Down"),
    ]

    issues = []
    for mask, message in cases:
        if mask.any():
            issues.append(f"{int(mask.sum())} linhas com {message}")
    return issues

def check_icd9_format(df):
    """Checa se os códigos de diagnóstico respeitam o formato ICD-9: três dígitos."""

    icd_columns = ("diag_1", "diag_2", "diag_3")

    pattern = r"^(\d{3}(\.\d{1,2})?|[EV]\d{2,3}(\.\d{1,2})?)$"
    issues = []
    for col in icd_columns:
        series = df[col]
        malformed = series[(series != "?") & ~series.str.match(pattern)]
        if not malformed.empty:
            issues.append(
                f"Coluna '{col}' possui {len(malformed)} códigos fora do formato ICD-9"
            )
    return issues


def check_diabetes_dataset(df):
    """Executa todas as checagens."""

    integer_columns = [
        "encounter_id", "patient_nbr", "admission_type_id",
        "discharge_disposition_id", "admission_source_id", "time_in_hospital",
        "num_lab_procedures", "num_procedures", "num_medications",
        "number_outpatient", "number_emergency", "number_inpatient",
        "number_diagnoses",
    ]
    expected_schema = {name: "int64" for name in integer_columns}
    bounds = {name: (0, float("inf")) for name in integer_columns}

    sentinels = ["?"] + PANDAS_NA

    tests = [
        check_column_names,
        partial(check_dtypes, expected_schema=expected_schema),
        partial(check_duplicate, key_column="encounter_id"),
        partial(check_sentinel_values, sentinels=sentinels),
        check_zero_variance,
        partial(check_numeric_bounds, bounds=bounds),
        check_medication_consistency,
        check_icd9_format,
    ]

    for test in tests:
        # Truque para obter o nome da função, mesmo que seja um partial
        name = getattr(test, "func", test).__name__
        issues = test(df)
        if issues:
            print(f"\nProblemas encontrados em {name}:")
        for issue in issues:
            print(issue)

