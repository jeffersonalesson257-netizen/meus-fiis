import React, { useState } from 'react';
import { Search, TrendingUp, TrendingDown, AlertCircle, Download, Star, Info, Activity, ArrowRightLeft, FileText, Bot } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { fetchFIIData, generateAIAnalysis, analyzeManagementReport } from '@/services/api';
import { FIIData, AIAnalysis, ReportAnalysisResult } from '@/types';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'comparador' | 'relatorio'>('dashboard');
  
  // Dashboard State
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [fiiData, setFiiData] = useState<FIIData | null>(null);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [error, setError] = useState('');
  
  // Real-time State
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [priceTrend, setPriceTrend] = useState<'up' | 'down' | 'neutral'>('neutral');

  // Comparator State
  const [tickerA, setTickerA] = useState('');
  const [tickerB, setTickerB] = useState('');
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [fiiA, setFiiA] = useState<FIIData | null>(null);
  const [fiiB, setFiiB] = useState<FIIData | null>(null);
  const [errorCompare, setErrorCompare] = useState('');

  // Report Reading State
  const [reportText, setReportText] = useState('');
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportAnalysis, setReportAnalysis] = useState<ReportAnalysisResult | null>(null);
  const [errorReport, setErrorReport] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;

    setLoading(true);
    setError('');
    setFiiData(null);
    setAnalysis(null);
    setLivePrice(null);
    setPriceTrend('neutral');

    try {
      const data = await fetchFIIData(ticker);
      setFiiData(data);
      setLivePrice(data.price);
      const aiResult = await generateAIAnalysis(data);
      setAnalysis(aiResult);
    } catch (err) {
      console.error(err);
      setError('Erro ao buscar dados do FII. Verifique o código e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  // Real-time polling effect
  React.useEffect(() => {
    if (!fiiData || activeTab !== 'dashboard') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/fii/${fiiData.ticker}/quote`);
        if (!res.ok) return;
        const data = await res.json();
        
        setLivePrice(prev => {
          if (prev !== null) {
            if (data.price > prev) setPriceTrend('up');
            else if (data.price < prev) setPriceTrend('down');
            else setPriceTrend('neutral');
          }
          return data.price;
        });
      } catch (err) {
        console.error("Erro ao buscar cotação em tempo real", err);
      }
    }, 3000); // Poll every 3 seconds for a more "live" feel

    return () => clearInterval(interval);
  }, [fiiData, activeTab]);

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tickerA.trim() || !tickerB.trim()) return;

    setLoadingCompare(true);
    setErrorCompare('');
    setFiiA(null);
    setFiiB(null);

    try {
      const [dataA, dataB] = await Promise.all([
        fetchFIIData(tickerA),
        fetchFIIData(tickerB)
      ]);
      setFiiA(dataA);
      setFiiB(dataB);
    } catch (err) {
      console.error(err);
      setErrorCompare('Erro ao buscar dados para comparação. Verifique os códigos.');
    } finally {
      setLoadingCompare(false);
    }
  };

  const handleReportAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportText.trim()) return;

    setLoadingReport(true);
    setErrorReport('');
    setReportAnalysis(null);

    try {
      const result = await analyzeManagementReport(reportText);
      setReportAnalysis(result);
    } catch (err) {
      console.error(err);
      setErrorReport('Erro ao analisar o relatório. Tente novamente.');
    } finally {
      setLoadingReport(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('pt-BR').format(value);
  };

  const exportToPDF = () => {
    if (!fiiData || !analysis) return;

    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(20);
    doc.setTextColor(79, 70, 229); // Indigo 600
    doc.text(`Relatório de Análise: ${fiiData.ticker}`, 14, 22);
    
    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139); // Slate 500
    doc.text(`${fiiData.name} | ${fiiData.type} - ${fiiData.segment}`, 14, 30);

    // Key Metrics
    doc.setFontSize(14);
    doc.setTextColor(15, 23, 42); // Slate 900
    doc.text('Indicadores Principais', 14, 45);

    const metricsData = [
      ['Preço Atual', formatCurrency(livePrice || fiiData.price)],
      ['Dividend Yield (12m)', `${fiiData.dy}%`],
      ['P/VP', fiiData.pvp.toString()],
      ['Vacância', `${fiiData.vacancy}%`],
      ['Liquidez Diária', formatCurrency(fiiData.liquidity)],
      ['Cotistas', formatNumber(fiiData.shareholders)],
      ['Patrimônio Líquido', formatCurrency(fiiData.netWorth)],
    ];

    autoTable(doc, {
      startY: 50,
      head: [['Indicador', 'Valor']],
      body: metricsData,
      theme: 'striped',
      headStyles: { fillColor: [79, 70, 229] },
    });

    // AI Analysis
    const finalY = (doc as any).lastAutoTable?.finalY || 120;
    
    doc.setFontSize(14);
    doc.setTextColor(15, 23, 42);
    doc.text('Diagnóstico da IA', 14, finalY + 15);
    
    doc.setFontSize(11);
    doc.setTextColor(51, 65, 85);
    doc.text(`Classificação: ${analysis.diagnosis} (Score: ${analysis.score}/10)`, 14, finalY + 25);
    
    const splitRecommendation = doc.splitTextToSize(`Recomendação: ${analysis.recommendation}`, 180);
    doc.text(splitRecommendation, 14, finalY + 35);

    const splitExplanation = doc.splitTextToSize(`Sobre o Fundo: ${analysis.explanation}`, 180);
    doc.text(splitExplanation, 14, finalY + 35 + (splitRecommendation.length * 7));

    const splitReport = doc.splitTextToSize(`Análise do Relatório: ${analysis.reportAnalysis}`, 180);
    doc.text(splitReport, 14, finalY + 35 + (splitRecommendation.length * 7) + (splitExplanation.length * 7));

    doc.save(`analise_${fiiData.ticker}.pdf`);
  };

  const exportToExcel = () => {
    if (!fiiData || !analysis) return;

    const data = [
      ['Ticker', fiiData.ticker],
      ['Nome', fiiData.name],
      ['Tipo', fiiData.type],
      ['Segmento', fiiData.segment],
      ['Preço Atual', livePrice || fiiData.price],
      ['Dividend Yield (%)', fiiData.dy],
      ['P/VP', fiiData.pvp],
      ['Vacância (%)', fiiData.vacancy],
      ['Liquidez Diária', fiiData.liquidity],
      ['Cotistas', fiiData.shareholders],
      ['Patrimônio Líquido', fiiData.netWorth],
      [''],
      ['Diagnóstico IA', analysis.diagnosis],
      ['Score', analysis.score],
      ['Recomendação', analysis.recommendation],
      ['Explicação', analysis.explanation],
      ['Análise do Relatório', analysis.reportAnalysis],
      [''],
      ['Pontos Positivos', (analysis.pros || []).join('; ')],
      ['Pontos Negativos', (analysis.cons || []).join('; ')],
    ];

    const ws = XLSX.utils.aoa_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Análise FII');
    XLSX.writeFile(wb, `analise_${fiiData.ticker}.xlsx`);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b-0 border-white/[0.05]">
        <div className="container mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2.5 rounded-xl shadow-lg shadow-indigo-500/20">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">FII Analyzer <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Pro</span></h1>
          </div>
          <div className="hidden md:flex items-center bg-slate-900/50 p-1.5 rounded-2xl border border-white/[0.05]">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={cn("transition-all duration-300 flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium", activeTab === 'dashboard' ? "bg-indigo-500/20 text-indigo-300 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]")}
            >
              <Activity className="w-4 h-4" /> Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('comparador')}
              className={cn("transition-all duration-300 flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium", activeTab === 'comparador' ? "bg-indigo-500/20 text-indigo-300 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]")}
            >
              <ArrowRightLeft className="w-4 h-4" /> Comparador
            </button>
            <button 
              onClick={() => setActiveTab('relatorio')}
              className={cn("transition-all duration-300 flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium", activeTab === 'relatorio' ? "bg-indigo-500/20 text-indigo-300 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]")}
            >
              <FileText className="w-4 h-4" /> Leitura de Relatório
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 max-w-7xl flex-1">
        {activeTab === 'dashboard' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {/* Search Section */}
            <section className="mb-16 text-center max-w-3xl mx-auto">
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
                <h2 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight text-slate-100">
                  Análise Inteligente de <span className="text-gradient">FIIs</span>
                </h2>
                <p className="text-slate-400 mb-10 text-lg md:text-xl font-light">Digite o ticker do Fundo Imobiliário e receba um diagnóstico completo com inteligência artificial.</p>
                
                <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4 max-w-xl mx-auto relative">
                  <div className="relative flex-1 group">
                    <div className="absolute inset-0 bg-indigo-500/20 rounded-2xl blur-xl group-focus-within:bg-indigo-500/40 transition-all duration-500 opacity-50"></div>
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-slate-400 z-10" />
                    <Input 
                      placeholder="Ex: MXRF11, HGLG11..." 
                      className="pl-14 h-16 text-xl bg-slate-900/80 backdrop-blur-sm border-white/10 focus-visible:ring-indigo-500/50 focus-visible:border-indigo-500 uppercase rounded-2xl relative z-10 shadow-xl font-mono tracking-wider placeholder:font-sans placeholder:tracking-normal"
                      value={ticker}
                      onChange={(e) => setTicker(e.target.value)}
                      maxLength={6}
                    />
                  </div>
                  <Button type="submit" size="lg" className="h-16 px-10 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-xl shadow-indigo-900/20 rounded-2xl text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] relative z-10" disabled={loading}>
                    {loading ? 'Analisando...' : 'Analisar'}
                  </Button>
                </form>
                {error && <p className="text-rose-400 mt-6 text-sm font-medium bg-rose-500/10 py-2 px-4 rounded-lg inline-block border border-rose-500/20">{error}</p>}
              </motion.div>
            </section>

            {/* Results Section */}
            <AnimatePresence mode="wait">
              {fiiData && analysis && (
                <motion.div 
                  key="results"
                  initial={{ opacity: 0, y: 20 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-8"
                >
                  {/* Header Info */}
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-white/[0.05] pb-8">
                    <div>
                      <div className="flex items-center gap-4 mb-3">
                        <h2 className="text-5xl font-bold tracking-tight font-mono text-slate-100">{fiiData.ticker}</h2>
                        <span className="px-4 py-1.5 rounded-full bg-indigo-500/10 text-xs font-semibold text-indigo-300 border border-indigo-500/20 uppercase tracking-wider">
                          {fiiData.type} • {fiiData.segment}
                        </span>
                      </div>
                      <p className="text-slate-400 text-xl font-light">{fiiData.name}</p>
                    </div>
                    <div className="flex gap-3">
                      <Button variant="outline" className="gap-2 bg-slate-900/50 border-white/10 hover:bg-white/5 hover:text-slate-100 rounded-xl h-11">
                        <Star className="w-4 h-4" /> Favoritar
                      </Button>
                      <Button variant="outline" className="gap-2 bg-slate-900/50 border-white/10 hover:bg-white/5 hover:text-slate-100 rounded-xl h-11" onClick={exportToPDF}>
                        <Download className="w-4 h-4" /> PDF
                      </Button>
                      <Button variant="outline" className="gap-2 bg-slate-900/50 border-white/10 hover:bg-white/5 hover:text-slate-100 rounded-xl h-11" onClick={exportToExcel}>
                        <Download className="w-4 h-4" /> Excel
                      </Button>
                    </div>
                  </div>

                  {/* Key Metrics Grid */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricCard 
                      title="Preço Atual" 
                      value={formatCurrency(livePrice || fiiData.price)} 
                      trend={priceTrend} 
                      isLive={true}
                    />
                    <MetricCard title="Dividend Yield (12m)" value={`${fiiData.dy}%`} trend={fiiData.dy > 8 ? "up" : "neutral"} />
                    <MetricCard title="P/VP" value={fiiData.pvp.toString()} trend={fiiData.pvp < 1 ? "up" : fiiData.pvp > 1.05 ? "down" : "neutral"} />
                    <MetricCard title="Vacância" value={`${fiiData.vacancy}%`} trend={fiiData.vacancy < 5 ? "up" : fiiData.vacancy > 10 ? "down" : "neutral"} />
                    <MetricCard title="Liquidez Diária" value={formatCurrency(fiiData.liquidity)} />
                    <MetricCard title="Cotistas" value={formatNumber(fiiData.shareholders)} />
                    <MetricCard title="Patrimônio Líquido" value={formatCurrency(fiiData.netWorth)} className="col-span-2" />
                  </div>

                  {/* AI Analysis Section */}
                  <div className="grid md:grid-cols-3 gap-6">
                    <Card className="md:col-span-2 glass-panel ai-border overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none" />
                      <CardHeader className="relative z-10 border-b border-white/[0.05] pb-4">
                        <CardTitle className="flex items-center gap-2 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 text-xl">
                          <Bot className="w-6 h-6 text-indigo-400" /> Diagnóstico da IA
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-8 pt-6 relative z-10">
                        <div className="flex items-center justify-between p-5 rounded-2xl bg-black/20 border border-white/[0.05] backdrop-blur-sm">
                          <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Classificação Geral</p>
                            <p className={cn(
                              "text-3xl font-bold tracking-tight",
                              analysis.diagnosis === "FII Forte" ? "text-emerald-400" :
                              analysis.diagnosis === "FII Moderado" ? "text-amber-400" : "text-rose-400"
                            )}>
                              {analysis.diagnosis}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Score</p>
                            <div className="flex items-baseline gap-1">
                              <span className="text-4xl font-bold font-mono text-white">{analysis.score}</span>
                              <span className="text-slate-500 font-mono">/10</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Recomendação</h4>
                          <p className="text-slate-200 leading-relaxed text-lg font-light">{analysis.recommendation}</p>
                        </div>

                        <div className="grid sm:grid-cols-2 gap-6">
                          <div className="space-y-4 bg-emerald-500/5 p-5 rounded-2xl border border-emerald-500/10">
                            <h4 className="font-semibold text-emerald-400 flex items-center gap-2">
                              <TrendingUp className="w-5 h-5" /> Pontos Positivos
                            </h4>
                            <ul className="space-y-3">
                              {analysis.pros?.map((pro, i) => (
                                <li key={i} className="text-sm text-slate-300 flex items-start gap-3">
                                  <span className="text-emerald-500 mt-0.5 shrink-0">•</span> 
                                  <span className="leading-relaxed">{pro}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="space-y-4 bg-rose-500/5 p-5 rounded-2xl border border-rose-500/10">
                            <h4 className="font-semibold text-rose-400 flex items-center gap-2">
                              <TrendingDown className="w-5 h-5" /> Pontos de Atenção
                            </h4>
                            <ul className="space-y-3">
                              {analysis.cons?.map((con, i) => (
                                <li key={i} className="text-sm text-slate-300 flex items-start gap-3">
                                  <span className="text-rose-500 mt-0.5 shrink-0">•</span> 
                                  <span className="leading-relaxed">{con}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <div className="space-y-6">
                      <Card className="glass-panel h-full">
                        <CardHeader className="border-b border-white/[0.05] pb-4">
                          <CardTitle className="flex items-center gap-2 text-cyan-400 text-xl">
                            <Info className="w-6 h-6" /> Entenda o Fundo
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6 flex flex-col h-[calc(100%-70px)]">
                          <p className="text-sm text-slate-300 leading-relaxed flex-1">{analysis.explanation}</p>
                          
                          <div className="mt-8 p-5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 relative z-10">Simulador de Renda</h4>
                            <p className="text-xs text-slate-400 mb-3 relative z-10">Rendimento estimado para R$ 10.000 investidos:</p>
                            <div className="text-3xl font-bold font-mono text-white relative z-10">
                              {formatCurrency((10000 * (fiiData.dy / 100)) / 12)} <span className="text-sm font-sans font-normal text-slate-400">/mês</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Management Report Analysis */}
                    <Card className="md:col-span-3 glass-panel">
                      <CardHeader className="border-b border-white/[0.05] pb-4">
                        <CardTitle className="flex items-center gap-2 text-purple-400 text-xl">
                          <FileText className="w-6 h-6" /> Análise do Relatório Gerencial
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="pt-6">
                        <div className="p-6 rounded-2xl bg-black/20 border border-white/[0.05]">
                          <div className="mb-6">
                            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Trecho do Relatório</h4>
                            <p className="text-sm text-slate-400 italic border-l-4 border-slate-700/50 pl-4 py-1">"{fiiData.managementReport}"</p>
                          </div>
                          <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent my-6"></div>
                          <div>
                            <h4 className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                              <Bot className="w-4 h-4" /> Visão da IA
                            </h4>
                            <p className="text-base text-slate-300 leading-relaxed font-light">{analysis.reportAnalysis}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Charts Section */}
                  <div className="grid md:grid-cols-2 gap-6">
                    <Card className="glass-panel">
                      <CardHeader className="border-b border-white/[0.05] pb-4">
                        <CardTitle className="text-lg font-medium text-slate-200">Histórico de Preço (6 meses)</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[320px] pt-6">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={fiiData.history} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `R$ ${value}`} domain={['auto', 'auto']} dx={-10} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }}
                              itemStyle={{ color: '#e2e8f0', fontFamily: 'JetBrains Mono' }}
                              formatter={(value: number) => [formatCurrency(value), 'Preço']}
                            />
                            <Line type="monotone" dataKey="price" stroke="#818cf8" strokeWidth={3} dot={{ r: 4, fill: '#818cf8', strokeWidth: 0 }} activeDot={{ r: 6, fill: '#fff', stroke: '#818cf8', strokeWidth: 2 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card className="glass-panel">
                      <CardHeader className="border-b border-white/[0.05] pb-4">
                        <CardTitle className="text-lg font-medium text-slate-200">Histórico de Dividendos (6 meses)</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[320px] pt-6">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={fiiData.history} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `R$ ${value}`} dx={-10} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }}
                              itemStyle={{ color: '#e2e8f0', fontFamily: 'JetBrains Mono' }}
                              formatter={(value: number) => [formatCurrency(value), 'Dividendo']}
                              cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            />
                            <Bar dataKey="dividend" fill="#10b981" radius={[6, 6, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {activeTab === 'comparador' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <section className="mb-16 text-center max-w-3xl mx-auto">
              <h2 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight text-slate-100">
                Comparador de <span className="text-gradient">FIIs</span>
              </h2>
              <p className="text-slate-400 mb-10 text-lg md:text-xl font-light">Compare dois fundos imobiliários lado a lado e descubra a melhor opção para sua carteira.</p>
              
              <form onSubmit={handleCompare} className="flex flex-col sm:flex-row gap-4 max-w-3xl mx-auto items-center relative">
                <div className="absolute inset-0 bg-indigo-500/10 rounded-2xl blur-xl opacity-50"></div>
                <Input 
                  placeholder="Ticker A (ex: MXRF11)" 
                  className="h-16 text-xl bg-slate-900/80 backdrop-blur-sm border-white/10 focus-visible:ring-indigo-500/50 focus-visible:border-indigo-500 uppercase text-center rounded-2xl relative z-10 shadow-xl font-mono tracking-wider placeholder:font-sans placeholder:tracking-normal"
                  value={tickerA}
                  onChange={(e) => setTickerA(e.target.value)}
                  maxLength={6}
                />
                <div className="bg-indigo-500/10 p-3 rounded-full shrink-0 relative z-10 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                  <ArrowRightLeft className="w-6 h-6 text-indigo-400" />
                </div>
                <Input 
                  placeholder="Ticker B (ex: HGLG11)" 
                  className="h-16 text-xl bg-slate-900/80 backdrop-blur-sm border-white/10 focus-visible:ring-indigo-500/50 focus-visible:border-indigo-500 uppercase text-center rounded-2xl relative z-10 shadow-xl font-mono tracking-wider placeholder:font-sans placeholder:tracking-normal"
                  value={tickerB}
                  onChange={(e) => setTickerB(e.target.value)}
                  maxLength={6}
                />
                <Button type="submit" size="lg" className="h-16 px-10 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold w-full sm:w-auto rounded-2xl text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] relative z-10 shadow-xl shadow-indigo-900/20" disabled={loadingCompare}>
                  {loadingCompare ? 'Comparando...' : 'Comparar'}
                </Button>
              </form>
              {errorCompare && <p className="text-rose-400 mt-6 text-sm font-medium bg-rose-500/10 py-2 px-4 rounded-lg inline-block border border-rose-500/20">{errorCompare}</p>}
            </section>

            {fiiA && fiiB && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-8">
                  <Card className="glass-panel overflow-hidden">
                    <CardHeader className="text-center border-b border-white/[0.05] pb-6 bg-slate-900/50">
                      <CardTitle className="text-5xl font-bold font-mono text-slate-100 mb-2">{fiiA.ticker}</CardTitle>
                      <p className="text-slate-400 font-light text-lg">{fiiA.name}</p>
                      <span className="inline-block mt-4 px-4 py-1.5 rounded-full bg-indigo-500/10 text-xs font-semibold text-indigo-300 border border-indigo-500/20 uppercase tracking-wider">
                        {fiiA.type} • {fiiA.segment}
                      </span>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ComparisonRow label="Preço" valA={formatCurrency(fiiA.price)} />
                      <ComparisonRow label="Dividend Yield" valA={`${fiiA.dy}%`} isBetter={fiiA.dy > fiiB.dy} />
                      <ComparisonRow label="P/VP" valA={fiiA.pvp.toString()} isBetter={Math.abs(1 - fiiA.pvp) < Math.abs(1 - fiiB.pvp)} />
                      <ComparisonRow label="Vacância" valA={`${fiiA.vacancy}%`} isBetter={fiiA.vacancy < fiiB.vacancy} />
                      <ComparisonRow label="Liquidez Diária" valA={formatCurrency(fiiA.liquidity)} isBetter={fiiA.liquidity > fiiB.liquidity} />
                      <ComparisonRow label="Cotistas" valA={formatNumber(fiiA.shareholders)} isBetter={fiiA.shareholders > fiiB.shareholders} />
                    </CardContent>
                  </Card>

                  <Card className="glass-panel overflow-hidden">
                    <CardHeader className="text-center border-b border-white/[0.05] pb-6 bg-slate-900/50">
                      <CardTitle className="text-5xl font-bold font-mono text-slate-100 mb-2">{fiiB.ticker}</CardTitle>
                      <p className="text-slate-400 font-light text-lg">{fiiB.name}</p>
                      <span className="inline-block mt-4 px-4 py-1.5 rounded-full bg-indigo-500/10 text-xs font-semibold text-indigo-300 border border-indigo-500/20 uppercase tracking-wider">
                        {fiiB.type} • {fiiB.segment}
                      </span>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ComparisonRow label="Preço" valA={formatCurrency(fiiB.price)} />
                      <ComparisonRow label="Dividend Yield" valA={`${fiiB.dy}%`} isBetter={fiiB.dy > fiiA.dy} />
                      <ComparisonRow label="P/VP" valA={fiiB.pvp.toString()} isBetter={Math.abs(1 - fiiB.pvp) < Math.abs(1 - fiiA.pvp)} />
                      <ComparisonRow label="Vacância" valA={`${fiiB.vacancy}%`} isBetter={fiiB.vacancy < fiiA.vacancy} />
                      <ComparisonRow label="Liquidez Diária" valA={formatCurrency(fiiB.liquidity)} isBetter={fiiB.liquidity > fiiA.liquidity} />
                      <ComparisonRow label="Cotistas" valA={formatNumber(fiiB.shareholders)} isBetter={fiiB.shareholders > fiiA.shareholders} />
                    </CardContent>
                  </Card>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}

        {activeTab === 'relatorio' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <section className="mb-16 text-center max-w-4xl mx-auto">
              <h2 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight text-slate-100">
                Leitura de <span className="text-gradient">Relatório Gerencial</span>
              </h2>
              <p className="text-slate-400 mb-10 text-lg md:text-xl font-light">Cole o texto do relatório gerencial do seu FII e nossa IA fará a leitura e extrairá os pontos mais importantes.</p>
              
              <form onSubmit={handleReportAnalysis} className="flex flex-col gap-6 max-w-4xl mx-auto relative">
                <div className="absolute inset-0 bg-indigo-500/5 rounded-3xl blur-2xl opacity-50"></div>
                <Textarea 
                  placeholder="Cole aqui o texto extraído do PDF do relatório gerencial..." 
                  className="min-h-[240px] text-lg bg-slate-900/80 backdrop-blur-sm border-white/10 focus-visible:ring-indigo-500/50 focus-visible:border-indigo-500 resize-y rounded-2xl p-6 relative z-10 shadow-xl leading-relaxed"
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                />
                <Button type="submit" size="lg" className="h-16 px-10 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold w-full sm:w-auto self-end gap-3 rounded-2xl text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] relative z-10 shadow-xl shadow-indigo-900/20" disabled={loadingReport || !reportText.trim()}>
                  {loadingReport ? (
                    <>Analisando o documento...</>
                  ) : (
                    <><Bot className="w-6 h-6" /> Analisar com IA</>
                  )}
                </Button>
              </form>
              {errorReport && <p className="text-rose-400 mt-6 text-sm font-medium bg-rose-500/10 py-2 px-4 rounded-lg inline-block border border-rose-500/20">{errorReport}</p>}
            </section>

            {reportAnalysis && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-5xl mx-auto space-y-6">
                <Card className="glass-panel ai-border overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none" />
                  <CardHeader className="border-b border-white/[0.05] pb-6 relative z-10">
                    <CardTitle className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                      <span className="flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 text-2xl">
                        <Activity className="w-7 h-7 text-indigo-400" /> Resumo Executivo
                      </span>
                      <span className={cn(
                        "text-sm px-4 py-1.5 rounded-full border font-semibold tracking-wider uppercase shadow-lg",
                        reportAnalysis.managementTone === 'Otimista' ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-emerald-500/10" :
                        reportAnalysis.managementTone === 'Pessimista' ? "bg-rose-500/10 border-rose-500/30 text-rose-400 shadow-rose-500/10" :
                        "bg-slate-500/10 border-slate-500/30 text-slate-300 shadow-slate-500/10"
                      )}>
                        Tom da Gestão: {reportAnalysis.managementTone}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-8 space-y-10 relative z-10">
                    <div>
                      <p className="text-slate-200 leading-relaxed text-xl font-light">{reportAnalysis.summary}</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8">
                      <div className="space-y-5 bg-emerald-500/5 p-6 rounded-3xl border border-emerald-500/10">
                        <h4 className="font-semibold text-emerald-400 flex items-center gap-3 text-lg">
                          <TrendingUp className="w-6 h-6" /> Destaques Positivos
                        </h4>
                        <ul className="space-y-4">
                          {reportAnalysis.highlights?.map((item, i) => (
                            <li key={i} className="text-slate-300 flex items-start gap-4 bg-black/20 p-4 rounded-2xl border border-white/[0.02]">
                              <span className="text-emerald-500 mt-1 shrink-0">•</span> 
                              <span className="text-base leading-relaxed">{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="space-y-5 bg-rose-500/5 p-6 rounded-3xl border border-rose-500/10">
                        <h4 className="font-semibold text-rose-400 flex items-center gap-3 text-lg">
                          <AlertCircle className="w-6 h-6" /> Riscos e Desafios
                        </h4>
                        <ul className="space-y-4">
                          {reportAnalysis.risks?.map((item, i) => (
                            <li key={i} className="text-slate-300 flex items-start gap-4 bg-black/20 p-4 rounded-2xl border border-white/[0.02]">
                              <span className="text-rose-500 mt-1 shrink-0">•</span> 
                              <span className="text-base leading-relaxed">{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-3xl p-8 relative overflow-hidden group">
                      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                      <h4 className="font-semibold text-indigo-300 flex items-center gap-3 mb-4 text-lg relative z-10">
                        <Info className="w-6 h-6" /> Perspectiva de Dividendos (Guidance)
                      </h4>
                      <p className="text-slate-200 text-lg leading-relaxed font-light relative z-10">{reportAnalysis.dividendGuidance}</p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </motion.div>
        )}
      </main>
    </div>
  );
}

export function MetricCard({ title, value, trend, className, isLive }: { title: string, value: string, trend?: "up" | "down" | "neutral", className?: string, isLive?: boolean }) {
  return (
    <Card className={cn("glass-panel relative overflow-hidden group hover:border-indigo-500/30 transition-all duration-500", className)}>
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
      <CardContent className="p-6 flex flex-col justify-center h-full relative z-10">
        <div className="flex justify-between items-start mb-2">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
          {isLive && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400 uppercase tracking-wider shadow-[0_0_10px_rgba(16,185,129,0.2)]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Ao Vivo
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <h4 className={cn(
            "text-3xl font-bold font-mono tracking-tight transition-colors duration-300",
            isLive && trend === 'up' ? "text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]" :
            isLive && trend === 'down' ? "text-rose-400 drop-shadow-[0_0_8px_rgba(251,113,133,0.3)]" : "text-slate-100"
          )}>
            {value}
          </h4>
          {trend === "up" && <TrendingUp className="w-5 h-5 text-emerald-500" />}
          {trend === "down" && <TrendingDown className="w-5 h-5 text-rose-500" />}
          {trend === "neutral" && !isLive && <TrendingUp className="w-5 h-5 text-slate-600" />}
        </div>
      </CardContent>
    </Card>
  );
}

function ComparisonRow({ label, valA, isBetter }: { label: string, valA: string, isBetter?: boolean }) {
  return (
    <div className="flex justify-between items-center p-5 border-b border-white/[0.05] last:border-0 hover:bg-white/[0.02] transition-colors">
      <span className="text-sm font-medium text-slate-400 uppercase tracking-wider">{label}</span>
      <span className={cn("font-bold font-mono text-lg", isBetter ? "text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]" : "text-slate-200")}>
        {valA}
      </span>
    </div>
  );
}
