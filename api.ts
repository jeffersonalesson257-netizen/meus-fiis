import axios from "axios";
import { FIIData, AIAnalysis, ReportAnalysisResult } from "@/types";
import { GoogleGenAI } from "@google/genai";

export async function fetchFIIData(ticker: string): Promise<FIIData> {
  const response = await axios.get(`/api/fii/${ticker}`);
  return response.data;
}

export async function generateAIAnalysis(fii: FIIData): Promise<AIAnalysis> {
  try {
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    
    // Fallback if no API key is set, we'll generate a programmatic analysis
    if (!process.env.GEMINI_API_KEY || process.env.GEMINI_API_KEY === "MY_GEMINI_API_KEY") {
      return generateProgrammaticAnalysis(fii);
    }

    const prompt = `
      Atue como um analista sênior de Fundos Imobiliários (FIIs).
      Analise os seguintes dados do FII ${fii.ticker} (${fii.name}):
      - Tipo: ${fii.type}
      - Segmento: ${fii.segment}
      - Preço: R$ ${fii.price}
      - Dividend Yield (DY): ${fii.dy}%
      - P/VP: ${fii.pvp}
      - Liquidez Diária: R$ ${fii.liquidity}
      - Vacância: ${fii.vacancy}%
      - Trecho do Relatório Gerencial: "${fii.managementReport}"
      
      Retorne a análise ESTRITAMENTE no seguinte formato JSON, sem marcação markdown e sem texto adicional:
      {
        "pros": ["ponto positivo 1", "ponto positivo 2", "ponto positivo 3"],
        "cons": ["ponto negativo 1", "ponto negativo 2"],
        "diagnosis": "FII Forte" | "FII Moderado" | "FII Arriscado",
        "recommendation": "Sua recomendação detalhada aqui...",
        "explanation": "Explicação simples sobre a estratégia do fundo e riscos...",
        "reportAnalysis": "Análise crítica do trecho do relatório gerencial, destacando a visão da gestão e perspectivas...",
        "score": 8.5
      }
    `;

    const response = await ai.models.generateContent({
      model: "gemini-3.1-pro-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
      }
    });

    let text = response.text || "{}";
    const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      text = jsonMatch[1];
    } else {
      text = text.replace(/^```json\s*/, '').replace(/\s*```$/, '').trim();
    }
    const parsed = JSON.parse(text);
    
    return {
      pros: parsed.pros || [],
      cons: parsed.cons || [],
      diagnosis: parsed.diagnosis || "FII Moderado",
      recommendation: parsed.recommendation || "",
      explanation: parsed.explanation || "",
      reportAnalysis: parsed.reportAnalysis || "",
      score: parsed.score || 5
    } as AIAnalysis;
  } catch (error) {
    console.error("Error generating AI analysis:", error);
    return generateProgrammaticAnalysis(fii);
  }
}

function generateProgrammaticAnalysis(fii: FIIData): AIAnalysis {
  const pros: string[] = [];
  const cons: string[] = [];
  let score = 5;

  if (fii.dy > 10) {
    pros.push("Dividend Yield (DY) alto, indicando boa distribuição de rendimentos.");
    score += 1.5;
  } else if (fii.dy > 7) {
    pros.push("Dividend Yield (DY) atrativo e consistente.");
    score += 1;
  } else {
    cons.push("Dividend Yield (DY) abaixo da média do mercado.");
    score -= 1;
  }

  if (fii.pvp < 0.95) {
    pros.push("Negociado com desconto patrimonial (P/VP < 1).");
    score += 1.5;
  } else if (fii.pvp <= 1.05) {
    pros.push("Preço justo em relação ao valor patrimonial.");
    score += 0.5;
  } else {
    cons.push("Negociado com ágio (P/VP > 1.05), o que pode limitar o potencial de valorização.");
    score -= 1;
  }

  if (fii.vacancy < 5) {
    pros.push("Baixa vacância, demonstrando resiliência e boa gestão.");
    score += 1.5;
  } else if (fii.vacancy > 10) {
    cons.push("Vacância alta, o que pode impactar os rendimentos futuros.");
    score -= 1.5;
  }

  if (fii.liquidity > 1000000) {
    pros.push("Alta liquidez diária, facilitando a entrada e saída do fundo.");
    score += 0.5;
  } else {
    cons.push("Liquidez diária baixa, pode ser difícil vender grandes volumes.");
    score -= 1;
  }

  score = Math.max(0, Math.min(10, score));

  let diagnosis: "FII Forte" | "FII Moderado" | "FII Arriscado" = "FII Moderado";
  if (score >= 8) diagnosis = "FII Forte";
  else if (score < 5) diagnosis = "FII Arriscado";

  return {
    pros,
    cons,
    diagnosis,
    recommendation: score >= 8 
      ? "Excelente opção para compor carteira focada em renda passiva. O fundo apresenta fundamentos sólidos e boa relação risco-retorno."
      : score >= 5 
        ? "Fundo com fundamentos razoáveis, mas exige acompanhamento. Pode ser uma opção secundária na carteira."
        : "Fundo apresenta riscos elevados no momento. Recomendado cautela e análise aprofundada antes de investir.",
    explanation: `O ${fii.ticker} é um fundo do tipo ${fii.type} focado no segmento de ${fii.segment}. Sua estratégia principal é gerar renda através da exploração de seus ativos. Os principais riscos envolvem a vacância (atualmente em ${fii.vacancy}%) e oscilações na taxa de juros (Selic).`,
    reportAnalysis: `Análise automática do relatório: A gestão reportou o seguinte: "${fii.managementReport.substring(0, 150)}...". Em geral, o fundo demonstra foco na manutenção da rentabilidade e controle de riscos operacionais.`,
    score: parseFloat(score.toFixed(1))
  };
}

export async function analyzeManagementReport(reportText: string): Promise<ReportAnalysisResult> {
  try {
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    
    if (!process.env.GEMINI_API_KEY || process.env.GEMINI_API_KEY === "MY_GEMINI_API_KEY") {
      return generateProgrammaticReportAnalysis(reportText);
    }

    const prompt = `
      Atue como um analista sênior de Fundos Imobiliários (FIIs).
      Leia o seguinte texto extraído de um Relatório Gerencial e faça uma análise crítica.
      
      TEXTO DO RELATÓRIO:
      "${reportText}"
      
      Retorne a análise ESTRITAMENTE no seguinte formato JSON, sem marcação markdown e sem texto adicional:
      {
        "summary": "Resumo executivo do relatório em 2 ou 3 frases...",
        "managementTone": "Otimista" | "Neutro" | "Pessimista",
        "dividendGuidance": "O que a gestão fala sobre os próximos dividendos...",
        "risks": ["risco 1 citado", "risco 2 citado"],
        "highlights": ["destaque positivo 1", "destaque positivo 2"]
      }
    `;

    const response = await ai.models.generateContent({
      model: "gemini-3.1-pro-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
      }
    });

    let text = response.text || "{}";
    const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      text = jsonMatch[1];
    } else {
      text = text.replace(/^```json\s*/, '').replace(/\s*```$/, '').trim();
    }
    const parsed = JSON.parse(text);
    
    return {
      summary: parsed.summary || "",
      managementTone: parsed.managementTone || "Neutro",
      dividendGuidance: parsed.dividendGuidance || "",
      risks: parsed.risks || [],
      highlights: parsed.highlights || []
    } as ReportAnalysisResult;
  } catch (error) {
    console.error("Error generating report analysis:", error);
    return generateProgrammaticReportAnalysis(reportText);
  }
}

function generateProgrammaticReportAnalysis(text: string): ReportAnalysisResult {
  const lowerText = text.toLowerCase();
  let tone: "Otimista" | "Neutro" | "Pessimista" = "Neutro";
  
  if (lowerText.includes("crescimento") || lowerText.includes("aumento") || lowerText.includes("positivo") || lowerText.includes("superou")) {
    tone = "Otimista";
  } else if (lowerText.includes("queda") || lowerText.includes("desafio") || lowerText.includes("impacto negativo") || lowerText.includes("vacância aumentou")) {
    tone = "Pessimista";
  }

  return {
    summary: "A gestão apresenta os resultados do período focando na resiliência do portfólio. Foram destacadas as movimentações recentes e o impacto no resultado caixa do fundo.",
    managementTone: tone,
    dividendGuidance: "A expectativa é manter o patamar atual de distribuição, sujeito às condições macroeconômicas e recebimento dos aluguéis/juros.",
    risks: ["Risco de inadimplência de locatários/devedores", "Oscilação da taxa Selic impactando o custo de oportunidade"],
    highlights: ["Manutenção da taxa de ocupação", "Gestão ativa na renegociação de contratos"]
  };
}
