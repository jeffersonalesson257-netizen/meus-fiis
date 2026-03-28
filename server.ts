import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Stateful prices for real-time simulation
  const livePrices: Record<string, number> = {};

  // API Routes
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok" });
  });

  // Mock Data for FIIs
  const mockFIIs: Record<string, any> = {
    "HGLG11": {
      ticker: "HGLG11",
      name: "CGHG Logística",
      type: "Tijolo",
      segment: "Logística",
      price: 165.50,
      dy: 8.5,
      pvp: 1.05,
      liquidity: 4500000,
      vacancy: 4.2,
      shareholders: 350000,
      netWorth: 3500000000,
      managementReport: "O fundo manteve sua estratégia de alocação em galpões logísticos AAA. Neste mês, concluímos a renegociação do contrato com a locatária X, com reajuste de 5% acima da inflação. A vacância física permanece estável em 4.2%. O guidance de dividendos para o próximo semestre é de R$ 1,10 a R$ 1,15 por cota.",
      history: [
        { month: "Jan", price: 160, dividend: 1.10 },
        { month: "Fev", price: 162, dividend: 1.10 },
        { month: "Mar", price: 161, dividend: 1.10 },
        { month: "Abr", price: 164, dividend: 1.10 },
        { month: "Mai", price: 163, dividend: 1.10 },
        { month: "Jun", price: 165.50, dividend: 1.10 },
      ]
    },
    "MXRF11": {
      ticker: "MXRF11",
      name: "Maxi Renda",
      type: "Papel",
      segment: "Híbrido",
      price: 10.45,
      dy: 12.5,
      pvp: 1.02,
      liquidity: 12000000,
      vacancy: 0,
      shareholders: 1000000,
      netWorth: 2500000000,
      managementReport: "A gestão segue focada na originação de CRIs com boas garantias e taxas atrativas (IPCA + 7.5%). No mês, o fundo realizou o pré-pagamento de duas operações que geraram ganho de capital extraordinário, refletindo no leve aumento dos dividendos. A carteira de FIIs do fundo também apresentou valorização.",
      history: [
        { month: "Jan", price: 10.20, dividend: 0.11 },
        { month: "Fev", price: 10.30, dividend: 0.11 },
        { month: "Mar", price: 10.25, dividend: 0.12 },
        { month: "Abr", price: 10.40, dividend: 0.11 },
        { month: "Mai", price: 10.35, dividend: 0.11 },
        { month: "Jun", price: 10.45, dividend: 0.12 },
      ]
    },
    "KNRI11": {
      ticker: "KNRI11",
      name: "Kinea Renda Imobiliária",
      type: "Tijolo",
      segment: "Híbrido (Lajes e Logística)",
      price: 158.20,
      dy: 7.8,
      pvp: 0.98,
      liquidity: 3200000,
      vacancy: 2.5,
      shareholders: 250000,
      netWorth: 3800000000,
      managementReport: "O fundo assinou um novo contrato de locação no edifício Rochaverá, reduzindo a vacância do portfólio de lajes corporativas. No braço logístico, as operações seguem com 100% de ocupação e inadimplência zero. A gestão estuda novas aquisições no estado de São Paulo para o próximo trimestre.",
      history: [
        { month: "Jan", price: 155, dividend: 1.00 },
        { month: "Fev", price: 156, dividend: 1.00 },
        { month: "Mar", price: 154, dividend: 1.00 },
        { month: "Abr", price: 157, dividend: 1.00 },
        { month: "Mai", price: 159, dividend: 1.00 },
        { month: "Jun", price: 158.20, dividend: 1.00 },
      ]
    }
  };

  app.get("/api/fii/:ticker", (req, res) => {
    const ticker = req.params.ticker.toUpperCase();
    let data = mockFIIs[ticker];
    
    if (data) {
      if (!livePrices[ticker]) livePrices[ticker] = data.price;
      data = { ...data, price: livePrices[ticker] };
      res.json(data);
    } else {
      // Generate realistic mock data for unknown tickers
      const isPaper = Math.random() > 0.5;
      let price = livePrices[ticker];
      if (!price) {
        price = Math.random() * 100 + 10;
        livePrices[ticker] = parseFloat(price.toFixed(2));
      }
      
      const dy = Math.random() * 8 + 6; // 6% to 14%
      const pvp = Math.random() * 0.4 + 0.8; // 0.8 to 1.2
      const vacancy = isPaper ? 0 : Math.random() * 15;
      
      const generatedData = {
        ticker,
        name: `Fundo Imobiliário ${ticker}`,
        type: isPaper ? "Papel" : "Tijolo",
        segment: isPaper ? "Recebíveis" : "Lajes Corporativas",
        price: parseFloat(price.toFixed(2)),
        dy: parseFloat(dy.toFixed(2)),
        pvp: parseFloat(pvp.toFixed(2)),
        liquidity: Math.floor(Math.random() * 5000000) + 100000,
        vacancy: parseFloat(vacancy.toFixed(2)),
        shareholders: Math.floor(Math.random() * 200000) + 10000,
        netWorth: Math.floor(Math.random() * 2000000000) + 500000000,
        managementReport: `O fundo ${ticker} segue focado em sua tese de investimentos no segmento de ${isPaper ? "Recebíveis" : "Lajes Corporativas"}. A gestão destaca a resiliência do portfólio frente ao cenário macroeconômico atual. Não houve movimentações relevantes na carteira neste mês, e a distribuição de rendimentos segue em linha com o guidance.`,
        history: Array.from({ length: 6 }).map((_, i) => ({
          month: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"][i],
          price: parseFloat((livePrices[ticker] * (1 + (Math.random() * 0.1 - 0.05))).toFixed(2)),
          dividend: parseFloat(((livePrices[ticker] * (dy / 100)) / 12).toFixed(2))
        }))
      };
      res.json(generatedData);
    }
  });

  // Real-time quote endpoint
  app.get("/api/fii/:ticker/quote", (req, res) => {
    const ticker = req.params.ticker.toUpperCase();
    let currentPrice = livePrices[ticker];
    
    if (!currentPrice) {
      currentPrice = mockFIIs[ticker]?.price || (Math.random() * 100 + 10);
      livePrices[ticker] = currentPrice;
    }

    // Simulate real-time market fluctuation (-0.5% to +0.5%)
    const fluctuation = currentPrice * (Math.random() * 0.01 - 0.005);
    const newPrice = parseFloat((currentPrice + fluctuation).toFixed(2));
    livePrices[ticker] = newPrice;

    res.json({
      ticker,
      price: newPrice,
      timestamp: new Date().toISOString()
    });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
