# 📊 Painel Interativo de Criminalidade no Rio de Janeiro

Este aplicativo interativo permite visualizar dados de criminalidade no município do Rio de Janeiro com base em indicadores normalizados por delegacia (CISP) e distribuídos espacialmente por bairros.

---

## 🚀 Funcionalidades

- 🔎 Filtros por tipo de crime, ano, mês e bairro
- 📈 Visualização de taxas por 10 mil habitantes ou valores absolutos
- 🗺️ Mapa interativo com geolocalização por CISP
- 🎨 Interface com identidade visual personalizada (amarelo mostarda e cinza escuro)

---

## 🗂️ Estrutura do Projeto

📁 app/
├── app.py ← Código principal do aplicativo
├── requirements.txt ← Dependências para execução
└── data/
├── Base_Crimes_Com_Delegacia.csv
└── Limite_de_Bairros_Completo_Com_CISP.geojson


---

## 💡 Como Executar Localmente

1. Clone o repositório:
   
   git clone https://github.com/seu-usuario/app-crimes-rj.git
   cd app-crimes-rj
   
2. Instale as dependências:

pip install -r requirements.txt

3.Execute o app:

streamlit run app.py
