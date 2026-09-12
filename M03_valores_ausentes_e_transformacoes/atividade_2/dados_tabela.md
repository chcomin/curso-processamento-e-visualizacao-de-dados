# Descrição das variáveis do conjunto de dados

Descrições obtidas do site do UCI Machine Learning Repository: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008

| Nome da Variável | Papel | Tipo | Demografia | Descrição | Unidades | Valores Ausentes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `encounter_id` | ID | | | Identificador único de um atendimento/internação | | não |
| `patient_nbr` | ID | | | Identificador único de um paciente | | não |
| `race` | Atributo | Categórico | Raça | Valores: Caucasiano, Asiático, Afro-americano, Hispânico e outro | | sim |
| `gender` | Atributo | Categórico | Gênero | Valores: masculino, feminino e desconhecido/inválido | | não |
| `age` | Atributo | Categórico | Idade | Agrupado em intervalos de 10 anos: [0, 10), [10, 20),..., [90, 100) | | não |
| `weight` | Atributo | Categórico | | Peso em libras | libras | sim |
| `admission_type_id` | Atributo | Categórico | | Identificador numérico inteiro correspondente a 9 valores distintos, por exemplo: emergência, urgência, eletivo, recém-nascido e não disponível | | não |
| `discharge_disposition_id` | Atributo | Categórico | | Identificador numérico inteiro correspondente a 29 valores distintos, por exemplo: alta para casa, óbito e não disponível | | não |
| `admission_source_id` | Atributo | Categórico | | Identificador numérico inteiro correspondente a 21 valores distintos, por exemplo: encaminhamento médico, pronto-socorro e transferência de um hospital | | não |
| `time_in_hospital` | Atributo | Inteiro | | Número inteiro de dias entre a admissão e a alta | dias | não |
| `payer_code` | Atributo | Categórico | | Identificador numérico inteiro correspondente a 23 valores distintos, por exemplo: Blue Cross/Blue Shield, Medicare e pagamento próprio | | sim |
| `medical_specialty` | Atributo | Categórico | | Identificador numérico inteiro da especialidade do médico responsável pela admissão, correspondente a 84 valores distintos, por exemplo: cardiologia, medicina interna, clínica geral/medicina de família e cirurgião | | sim |
| `num_lab_procedures` | Atributo | Inteiro | | Número de exames laboratoriais realizados durante o atendimento | | não |
| `num_procedures` | Atributo | Inteiro | | Número de procedimentos (além de exames laboratoriais) realizados durante o atendimento | | não |
| `num_medications` | Atributo | Inteiro | | Número de nomes genéricos distintos administrados durante o atendimento | | não |
| `number_outpatient` | Atributo | Inteiro | | Número de consultas ambulatoriais do paciente no ano anterior ao atendimento | | não |
| `number_emergency` | Atributo | Inteiro | | Número de atendimentos de emergência do paciente no ano anterior ao atendimento | | não |
| `number_inpatient` | Atributo | Inteiro | | Número de internações do paciente no ano anterior ao atendimento | | não |
| `diag_1` | Atributo | Categórico | | Diagnóstico primário (codificado com os três primeiros dígitos do CID-9); 848 valores distintos | | sim |
| `diag_2` | Atributo | Categórico | | Diagnóstico secundário (codificado com os três primeiros dígitos do CID-9); 923 valores distintos | | sim |
| `diag_3` | Atributo | Categórico | | Diagnóstico secundário adicional (codificado com os três primeiros dígitos do CID-9); 954 valores distintos | | sim |
| `number_diagnoses` | Atributo | Inteiro | | Número de diagnósticos inseridos no sistema | | não |
| `max_glu_serum` | Atributo | Categórico | | Indica a faixa de resultado ou se o teste não foi realizado. Valores: >200, >300, normal e nenhum (caso não tenha sido medido) | | não |
| `A1Cresult` | Atributo | Categórico | | Indica a faixa do resultado ou se o teste não foi realizado. Valores: >8 se o resultado foi maior que 8%, >7 se o resultado foi maior que 7% mas menor que 8%, normal se o resultado foi menor que 7%, e nenhum se não medido. | | não |
| `metformin`, `repaglinide`, `nateglinide`, `chlorpropamide`, `glimepiride`, `acetohexamide`, `glipizide`, `glyburide`, `tolbutamide`, `pioglitazone`, `rosiglitazone`, `acarbose`, `miglitol`, `troglitazone`, `tolazamide`, `examide`, `citoglipton`, `insulin`, `glyburide-metformin`, `glipizide-metformin`, `glimepiride-pioglitazone`, `metformin-rosiglitazone` e `metformin-pioglitazone` | Atributo | Categórico | | 23 colunas que representam diferentes medicamentos para diabetes. Cada coluna indica se o medicamento foi prescrito ou se houve alteração na dosagem. Valores: "up" se a dosagem aumentou durante a internação, "down" se diminuiu, "steady" se permaneceu inalterada e "no" se não foi prescrito | | não |
| `change` | Atributo | Categórico | | Indica se houve alteração nas medicações para diabetes (seja na dosagem ou no princípio ativo/genérico). Valores: "change" (mudança) e "no change" (sem mudança) | | não |
| `diabetesMed` | Atributo | Categórico | | Indica se foi prescrito algum medicamento para diabetes. Valores: "yes" (sim) e "no" (não) | | não |
| `readmitted` | Alvo | Categórico | | Dias até a readmissão hospitalar do paciente. Valores: <30 se o paciente foi readmitido em menos de 30 dias, >30 se foi readmitido em mais de 30 dias, e "No" para nenhum registro de readmissão. | | não |