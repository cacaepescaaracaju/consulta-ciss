const dataFiles = [
  { name: "Cardoso", path: "./data/Cardoso.json" },
  { name: "Machado", path: "./data/Machado.json" },
];

const state = {
  all: [],
  query: "",
  hasSearched: false,
  updatedAtText: "",
  updatedAtDate: "",
};

const elements = {
  updatedAt: document.getElementById("updatedAt"),
  results: document.getElementById("results"),
  search: document.getElementById("search"),
  searchBtn: document.getElementById("searchBtn"),
  clearBtn: document.getElementById("clearBtn"),
};

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") return "";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toLocaleString("pt-BR");
}

function resolveEmpresa(idEmpresa) {
  if (Number(idEmpresa) === 1) return "Machado";
  if (Number(idEmpresa) === 2) return "Cardoso";
  return "Desconhecida";
}

function normalizeRecords(json) {
  const rows = [];
  Object.entries(json).forEach(([sheetName, list]) => {
    if (!Array.isArray(list)) return;
    list.forEach((item) => {
      rows.push({
        sheet: sheetName,
        IDEMPRESA: item.IDEMPRESA ?? "",
        EMPRESA: resolveEmpresa(item.IDEMPRESA),
        IDPRODUTO: item.IDPRODUTO ?? "",
        IDSUBPRODUTO: item.IDSUBPRODUTO ?? "",
        DESCRICAO: String(item.DESCRICAO ?? "").trim(),
        EMBALAGEMSAIDA: item.EMBALAGEMSAIDA ?? "",
        VALPRECOVAREJO: item.VALPRECOVAREJO ?? "",
        QTDATUALESTOQUE: item.QTDATUALESTOQUE ?? "",
        VALTOTAL: item.VALTOTAL ?? "",
      });
    });
  });
  return rows;
}

async function loadData() {
  const [att, ...datasets] = await Promise.all([
    fetch("./data/data_att.json").then((r) => r.json()),
    ...dataFiles.map((f) => fetch(f.path).then((r) => r.json())),
  ]);

  const updatedAt = new Date(att.updated_at);
  if (Number.isNaN(updatedAt.getTime())) {
    elements.updatedAt.textContent = att.updated_at;
    state.updatedAtText = att.updated_at;
    state.updatedAtDate = att.updated_at;
  } else {
    elements.updatedAt.textContent = updatedAt.toLocaleString("pt-BR");
    state.updatedAtText = updatedAt.toLocaleString("pt-BR");
    state.updatedAtDate = updatedAt.toLocaleDateString("pt-BR");
  }

  const all = datasets.flatMap((json) => normalizeRecords(json));
  state.all = all;
  render([]);
}

function searchProducts() {
  const raw = state.query.trim();
  state.hasSearched = true;
  if (!raw) {
    render([]);
    return;
  }

  const isNumeric = /^\d+$/.test(raw);
  const isDescricao = raw.startsWith("%") || !isNumeric;
  const query = raw.startsWith("%") ? raw.slice(1).trim().toLowerCase() : raw.toLowerCase();
  if (isDescricao && !query) {
    render([]);
    return;
  }

  const results = state.all.filter((item) => {
    if (isDescricao) {
      return String(item.DESCRICAO).toLowerCase().includes(query);
    }
    return String(item.IDPRODUTO) === raw;
  });

  render(results);
}

function render(items) {
  if (!items.length) {
    elements.results.innerHTML = state.hasSearched
      ? `<div class="empty">Nenhum resultado</div>`
      : `<div class="empty">Digite um termo e clique em Pesquisar</div>`;
    return;
  }

  elements.results.innerHTML = items
    .map((r) => {
      const qtd = Number(r.QTDATUALESTOQUE) || 0;
      const nameClass = qtd > 0 ? "name-positive" : "name-negative";
      return `
        <article class="card">
          <h2 class="${nameClass}">${r.DESCRICAO}</h2>
          <h5 class="muted">Código: ${r.IDPRODUTO} | Empresa: ${r.EMPRESA}</h5>
          <h3>${formatCurrency(r.VALPRECOVAREJO)}</h3>
          <h4>Embalagem: ${r.EMBALAGEMSAIDA}</h4>
          <h4>Saldo em estoque: ${formatNumber(r.QTDATUALESTOQUE)} <span class="updated-tag">em ${state.updatedAtDate}</span></h4>
        </article>
      `;
    })
    .join("");
}

elements.search.addEventListener("input", (e) => {
  state.query = e.target.value;
});

elements.searchBtn.addEventListener("click", () => {
  searchProducts();
});

elements.clearBtn.addEventListener("click", () => {
  state.query = "";
  state.hasSearched = false;
  elements.search.value = "";
  render([]);
});

elements.search.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    searchProducts();
  }
});

loadData().catch(() => {
  elements.updatedAt.textContent = "Falha ao carregar dados";
  elements.results.innerHTML = `<div class="empty">Erro ao carregar JSONs</div>`;
});
