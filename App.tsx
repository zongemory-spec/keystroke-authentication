
import React, { useState, useEffect } from 'react';
import { Lock, Shield, Terminal, Database, ChevronRight, AlertTriangle, Eye, EyeOff, BookOpen, Ghost, Zap, Bug, Radio, Cpu, FileText } from 'lucide-react';
import { User, SecurityView, ArchiveDocument } from './types';
import { executeVulnerableLogin } from './database';
import { getDemoArchiveContent } from './services/archiveService';

const App: React.FC = () => {
  const [view, setView] = useState<SecurityView>(SecurityView.LOGIN);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [lastQuery, setLastQuery] = useState('');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [archiveDocs, setArchiveDocs] = useState<ArchiveDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [simulation, setSimulation] = useState<'normal' | 'tautology' | 'comment'>('normal');
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = (e?: React.FormEvent) => {
    e?.preventDefault();
    setError('');
    
    const result = executeVulnerableLogin(username, password);
    setLastQuery(result.executedQuery);

    if (result.success && result.rows.length > 0) {
      setSimulation(result.simulation ?? 'normal');
      setCurrentUser(result.rows[0]);
      setView(SecurityView.DASHBOARD);
      fetchArchiveData(result.rows[0].role);
    } else {
      setError(result.error || '身份验证失败：访问被拒绝');
    }
  };

  const fetchArchiveData = async (role: string) => {
    setLoading(true);
    const docs = await getDemoArchiveContent(role);
    setArchiveDocs(docs);
    setLoading(false);
  };

  const quickExploit = (payload: string) => {
    setUsername(payload);
    setPassword('');
    setError('');
  };

  const logout = () => {
    setCurrentUser(null);
    setView(SecurityView.LOGIN);
    setUsername('');
    setPassword('');
    setLastQuery('');
    setError('');
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-zinc-300">
      {/* 全局氛围特效 */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="scanline"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(34,197,94,0.05)_0%,_rgba(0,0,0,0)_70%)]"></div>
      </div>

      <header className="z-10 bg-zinc-950/90 border-b border-emerald-900/30 p-4 backdrop-blur-md sticky top-0 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="bg-emerald-500/10 p-2 rounded border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
              <Cpu className="w-6 h-6 text-emerald-500" />
            </div>
            <div>
              <h1 className="text-xl font-black tracking-tighter text-zinc-100 uppercase italic">
                Aegis <span className="text-emerald-500">Vault</span> Node_7
              </h1>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                <p className="text-[9px] mono text-emerald-500/70 uppercase tracking-[0.2em]">合成数据 · 本地教学演示</p>
              </div>
            </div>
          </div>

          <nav className="flex items-center gap-3">
            <button 
              onClick={() => setView(SecurityView.LAB_GUIDE)}
              className="flex items-center gap-2 text-[10px] font-bold px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:border-emerald-500/50 transition-all uppercase"
            >
              <BookOpen className="w-3.5 h-3.5" />
              漏洞手册
            </button>
            {currentUser && (
              <button onClick={logout} className="text-[10px] font-bold px-3 py-1.5 rounded bg-red-950/30 border border-red-900/50 text-red-500 hover:bg-red-900 transition-all uppercase">
                紧急断开
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1 z-10 p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* 左侧主要区域 */}
        <div className="lg:col-span-8 space-y-6">
          {view === SecurityView.LOGIN && (
            <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl overflow-hidden backdrop-blur-md shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-700">
              <div className="p-6 border-b border-zinc-800 bg-zinc-900/60 flex justify-between items-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent"></div>
                <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-3">
                  <Radio className="w-5 h-5 text-emerald-500 animate-pulse" /> 
                  身份验证网关
                </h2>
                <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/20 rounded text-[9px] text-red-500 font-black tracking-widest uppercase">
                  <Bug className="w-3 h-3" /> SQL_拼接漏洞确认
                </div>
              </div>

              <div className="p-8">
                <form onSubmit={handleLogin} className="space-y-6 max-w-md mx-auto">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">用户名 / 注入载荷</label>
                    <div className="relative group">
                      <Terminal className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-emerald-500 transition-colors" />
                      <input 
                        type="text" 
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="输入 ' OR '1'='1 绕过"
                        className="w-full bg-zinc-950/50 border border-zinc-800 rounded py-3 pl-10 pr-4 focus:border-emerald-500/50 outline-none transition-all mono text-sm text-zinc-200"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">访问密码</label>
                    <div className="relative group">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-emerald-500 transition-colors" />
                      <input 
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full bg-zinc-950/50 border border-zinc-800 rounded py-3 pl-10 pr-12 focus:border-emerald-500/50 outline-none transition-all mono text-sm text-zinc-200"
                      />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-400">
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {error && (
                    <div className="p-4 rounded bg-red-950/20 border border-red-500/30 text-red-400 text-[11px] flex items-start gap-3 animate-pulse">
                      <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold uppercase tracking-tight mb-1">系统警报</p>
                        <p className="opacity-80 leading-relaxed font-mono">{error}</p>
                      </div>
                    </div>
                  )}

                  <button type="submit" className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 text-black font-black uppercase tracking-tighter rounded transition-all shadow-[0_0_20px_rgba(16,185,129,0.2)] flex justify-center items-center gap-2 group active:scale-[0.98]">
                    尝试建立连接
                    <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </form>

                <div className="mt-12 pt-8 border-t border-zinc-800/50">
                  <h3 className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
                    <Zap className="w-3 h-3 text-yellow-500" /> 渗透载荷库 (快捷填充)
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button onClick={() => quickExploit("' OR '1'='1")} className="text-left p-4 bg-zinc-950/80 border border-zinc-800 rounded hover:border-blue-500/50 transition-all group border-l-4 border-l-blue-900">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[9px] text-blue-500 font-bold uppercase">逻辑绕过</span>
                        <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                      </div>
                      <code className="text-xs text-blue-400 mono">' OR '1'='1</code>
                    </button>
                    <button onClick={() => quickExploit("admin' -- ")} className="text-left p-4 bg-zinc-950/80 border border-zinc-800 rounded hover:border-orange-500/50 transition-all group border-l-4 border-l-orange-900">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[9px] text-orange-500 font-bold uppercase">账号截断</span>
                        <div className="w-1 h-1 bg-orange-500 rounded-full"></div>
                      </div>
                      <code className="text-xs text-orange-400 mono">admin' -- </code>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {view === SecurityView.DASHBOARD && currentUser && (
            <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
              {/* 成功入侵的横幅 */}
              <div className="bg-emerald-950/20 border border-emerald-500/30 p-8 rounded-xl flex flex-col sm:flex-row items-center gap-8 backdrop-blur-md relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-2 bg-emerald-500 text-black text-[10px] font-black uppercase transform rotate-45 translate-x-10 -translate-y-2 w-40 text-center shadow-2xl">
                  {simulation === 'normal' ? 'DEMO LOGIN ACCEPTED' : 'SIMULATED BYPASS'}
                </div>
                <div className="bg-emerald-500/10 p-5 rounded-full border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
                  <Ghost className="w-12 h-12 text-emerald-400 animate-pulse" />
                </div>
                <div className="flex-1 text-center sm:text-left">
                  <h2 className="text-3xl font-black text-white uppercase italic tracking-tighter mb-1">
                    {simulation === 'normal' ? '模拟登录成功:' : '模拟绕过成功:'} <span className="text-emerald-500">{currentUser.username}</span>
                  </h2>
                  <div className="flex flex-wrap justify-center sm:justify-start gap-4">
                    <p className="text-emerald-400/80 text-[10px] mono uppercase tracking-widest flex items-center gap-2">
                      <Shield className="w-3 h-3" /> 权限: {currentUser.role}
                    </p>
                    <p className="text-zinc-500 text-[10px] mono uppercase tracking-widest flex items-center gap-2">
                      <Database className="w-3 h-3" /> 节点: NODE_7_DC
                    </p>
                  </div>
                </div>
              </div>

              {/* 核心机密 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 shadow-xl relative overflow-hidden group">
                  <div className="absolute -top-10 -right-10 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-all"></div>
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-500" /> 用户数据库字段 [secret_data]
                  </h3>
                  <div className="p-5 bg-black/60 rounded border border-zinc-800/50 italic text-emerald-100 text-lg leading-relaxed border-l-4 border-l-emerald-500 shadow-inner font-serif">
                    "{currentUser.secret_data}"
                  </div>
                </div>

                <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col">
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500" /> 本次查询分析
                  </h3>
                  <div className="flex-1 space-y-4">
                    <div className="space-y-2">
                      <p className="text-[10px] text-zinc-500 uppercase font-bold">拼接后的 SQL 语句：</p>
                      <div className="p-3 bg-black/80 rounded mono text-[11px] text-red-400 break-all border border-red-900/20 leading-tight">
                        {lastQuery}
                      </div>
                    </div>
                    <p className="text-[11px] text-zinc-400 italic bg-red-950/10 p-3 rounded border border-red-900/20 leading-relaxed">
                      {simulation === 'normal'
                        ? '本次使用匹配的演示账号和密码，模拟正常登录，没有触发注入规则。'
                        : simulation === 'comment'
                          ? '本次输入命中了注释截断模拟规则，演示用户输入可能改变拼接语句的含义；没有执行真实 SQL。'
                          : '本次输入命中了恒真式模拟规则，演示用户输入可能改变拼接语句的含义；没有执行真实 SQL。'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 本地虚构档案 */}
              <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/60 backdrop-blur-sm">
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <Database className="w-4 h-4 text-emerald-500" /> 关联解密档案 (Deep_Intelligence)
                  </h3>
                  {loading && <div className="flex items-center gap-2 text-[10px] text-emerald-500 animate-pulse font-mono">
                    <div className="animate-spin h-3 w-3 border-2 border-emerald-500 border-t-transparent rounded-full"></div>
                    解密中...
                  </div>}
                </div>
                <div className="p-6 space-y-4 max-h-[500px] overflow-y-auto custom-scrollbar">
                  {archiveDocs.map((doc, idx) => (
                    <div key={idx} className="p-6 bg-zinc-950/80 border border-zinc-800 rounded-lg border-l-4 border-l-emerald-900 hover:border-l-emerald-500 transition-all group relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl -translate-y-16 translate-x-16"></div>
                      <div className="flex justify-between items-start mb-3 relative z-10">
                        <h4 className="text-emerald-400 font-black uppercase tracking-tight text-lg italic">{doc.title}</h4>
                        <span className="px-2 py-1 bg-red-950/40 text-red-500 text-[9px] rounded border border-red-900 uppercase font-black tracking-tighter">
                          密级: {doc.classification}
                        </span>
                      </div>
                      <p className="text-zinc-400 text-xs leading-relaxed mb-6 font-mono relative z-10">
                        {doc.content}
                      </p>
                      <div className="flex justify-between items-center text-[9px] mono text-zinc-600 border-t border-zinc-900 pt-4 relative z-10">
                        <div className="flex gap-4">
                          <span>REF_ID: {Math.random().toString(16).slice(2, 10).toUpperCase()}</span>
                          <span>SIG: SIGNED_OFF_DIRECTOR</span>
                        </div>
                        <span className="text-zinc-500">归档日期: {doc.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {view === SecurityView.LAB_GUIDE && (
            <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-10 space-y-8 animate-in fade-in duration-500 backdrop-blur-md">
              <div className="border-b border-zinc-800 pb-8">
                <h2 className="text-4xl font-black text-white mb-2 uppercase italic tracking-tighter flex items-center gap-4">
                  SQL Injection <span className="text-emerald-500 underline decoration-double underline-offset-8">Lab_Guide</span>
                </h2>
                <p className="text-zinc-400 font-mono italic">“在网络战争中，代码就是武器。”</p>
              </div>

              <div className="grid grid-cols-1 gap-10">
                <section className="bg-zinc-950/50 p-8 rounded-lg border border-zinc-800 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-5">
                    <Database className="w-24 h-24" />
                  </div>
                  <h3 className="text-xl font-bold text-emerald-400 mb-4 flex items-center gap-3 italic">
                    <div className="w-1 h-6 bg-emerald-500"></div> 逻辑破坏攻击 (Tautology)
                  </h3>
                  <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
                    这是最经典的注入方式。当后端系统简单地使用 <code className="text-emerald-500 bg-emerald-950/30 px-1 rounded">username = '$input'</code> 进行匹配时，你可以通过输入单引号来提前结束字符串。
                  </p>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="bg-black/50 p-5 rounded border border-zinc-800">
                      <p className="text-[9px] text-zinc-500 uppercase font-bold mb-2">原始 SQL 指令</p>
                      <code className="text-[11px] mono text-zinc-400 italic">SELECT * FROM users WHERE user = 'admin' AND pass = '???'</code>
                    </div>
                    <div className="bg-black/80 p-5 rounded border border-emerald-900/30">
                      <p className="text-[9px] text-emerald-500 uppercase font-bold mb-2">注入后指令</p>
                      <code className="text-[11px] mono text-emerald-400">SELECT * FROM users WHERE user = <span className="text-white underline">'' OR '1'='1'</span> -- '</code>
                    </div>
                  </div>
                </section>

                <section className="bg-zinc-950/50 p-8 rounded-lg border border-zinc-800">
                  <h3 className="text-xl font-bold text-orange-400 mb-4 flex items-center gap-3 italic">
                    <div className="w-1 h-6 bg-orange-500"></div> 防御方案：参数化查询
                  </h3>
                  <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
                    真正的防御不是过滤，而是“隔离”。使用预编译语句，数据库会将输入视为纯文本参数，而永远不会将其解释为 SQL 命令的一部分。
                  </p>
                  <div className="bg-zinc-900 p-4 rounded mono text-[10px] text-zinc-500 border border-zinc-800 leading-relaxed">
                    <span className="text-blue-400">// 安全写法示例 (Node.js)</span><br/>
                    const query = <span className="text-emerald-500">"SELECT * FROM users WHERE username = ?"</span>;<br/>
                    db.execute(query, [userInput]);
                  </div>
                </section>
              </div>

              <div className="pt-8 border-t border-zinc-800 flex justify-end">
                <button onClick={() => setView(SecurityView.LOGIN)} className="px-10 py-4 bg-emerald-600 rounded text-black font-black uppercase tracking-widest hover:bg-emerald-500 transition-all shadow-xl active:scale-95">
                  准备好了，开始入侵
                </button>
              </div>
            </div>
          )}
        </div>

        {/* 右侧边栏：任务简报 (想象力增强点) */}
        <aside className="lg:col-span-4 space-y-6 sticky top-24">
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-6 backdrop-blur-md shadow-xl relative overflow-hidden border-l-4 border-l-emerald-500">
            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.3em] mb-6 flex items-center gap-2">
              <Radio className="w-4 h-4 text-emerald-500" /> 任务简报：OPER_VAULT
            </h3>
            <div className="space-y-6">
              <div className="p-4 bg-zinc-950/50 rounded border border-zinc-800/50">
                <p className="text-[11px] text-emerald-400/80 mb-2 font-bold uppercase tracking-tighter underline">目标简介</p>
                <p className="text-[10px] text-zinc-400 leading-relaxed italic">
                  “根据情报，Aegis 系统的后端代码由实习生在 2012 年编写，存在严重的逻辑拼接漏洞。你的任务是利用 SQL 注入获取其数据库内的核心机密。”
                </p>
              </div>
              
              <div className="space-y-3 text-[10px] mono">
                <div className="flex justify-between items-center text-zinc-500">
                  <span>当前状态:</span>
                  <span className="text-emerald-500 font-bold">待命 (STANDBY)</span>
                </div>
                <div className="flex justify-between items-center text-zinc-500">
                  <span>数据来源:</span>
                  <span>本地合成</span>
                </div>
                <div className="flex justify-between items-center text-zinc-500">
                  <span>执行方式:</span>
                  <span className="text-emerald-500">规则模拟</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-6 backdrop-blur-md relative overflow-hidden">
            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-500" /> 实时数据流监视器
            </h3>
            <div className="space-y-4">
              <div className="p-4 bg-black/80 rounded border border-zinc-800 mono text-[10px] leading-relaxed break-all relative">
                <div className="absolute top-0 right-0 p-1 text-[8px] text-zinc-700">LOG_v.2.0</div>
                {lastQuery ? (
                   <div className="animate-in fade-in space-y-1">
                      <p className="text-emerald-500/50">OUTGOING_STDOUT &gt;&gt;</p>
                      <p className="text-zinc-300 leading-tight italic">{lastQuery}</p>
                   </div>
                ) : (
                   <span className="text-zinc-800 italic animate-pulse">等待注入拦截请求...</span>
                )}
              </div>
            </div>
          </div>

          <div className="bg-emerald-950/10 border border-emerald-900/20 rounded-xl p-6">
            <h3 className="text-emerald-500 font-black text-[10px] mb-3 flex items-center gap-2 uppercase tracking-[0.2em]">
              <Zap className="w-4 h-4" /> 专家提示 (ProTip)
            </h3>
            <p className="text-zinc-400 text-[10px] leading-relaxed">
              在真实场景中，SQL 注入还可以用来 <strong>删表 (DROP TABLE)</strong> 或 <strong>导出整个数据库 (UNION SELECT)</strong>。本实验室专注于逻辑绕过。
            </p>
          </div>
        </aside>
      </main>

      <footer className="z-10 p-8 text-center border-t border-zinc-800 bg-zinc-950/80 mt-12 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-left">
              <p className="text-[10px] mono text-zinc-600 uppercase tracking-[0.4em] mb-1">
                Aegis_Global_Security_Infrastructure_v7.4
              </p>
              <p className="text-[8px] text-zinc-800 mono uppercase">Local teaching simulator · No database connection</p>
            </div>
            <div className="flex gap-6 grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all">
               <Shield className="w-5 h-5 text-emerald-500" />
               <Database className="w-5 h-5 text-emerald-500" />
               <Terminal className="w-5 h-5 text-emerald-500" />
            </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
