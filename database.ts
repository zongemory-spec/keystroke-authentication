
import { User, SQLQueryResult } from './types';

// 模拟数据库数据
const MOCK_USERS: User[] = [
  { id: 1, username: 'admin', role: 'SuperUser', secret_data: '核心机密：地下基地的入口密码是 8848。' },
  { id: 2, username: 'dr_vance', role: 'Researcher', secret_data: '实验记录：样本-09 在接触红光时表现出异常活跃。' },
  { id: 3, username: 'sarah_k', role: 'Archivist', secret_data: '历史档案：1947 年的事件并非陨石，而是某种未知的推进器。' }
];

/**
 * 模拟存在漏洞的后端查询函数
 */
export const executeVulnerableLogin = (username: string, password: string): SQLQueryResult => {
  // 构造拼接后的查询语句（模拟漏洞核心）
  const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}';`;
  
  const lowerUsername = username.toLowerCase().trim();
  const lowerPassword = password.toLowerCase().trim();

  // --- 1. 优先检测 SQL 注入攻击模式 ---
  
  // 模式 A: 恒真式绕过 (例如: ' OR '1'='1, ' OR 1=1, " OR "a"="a)
  // 这个正则现在更宽容，允许首尾有没有引号，允许任意数字/字符相等
  const alwaysTruePattern = /(['"]?)\s*OR\s+(['"]?).+?\2\s*=\s*\2.+?\2/i;
  
  // 模式 B: 注释截断 (例如: admin' --)
  const commentPattern = /['"]?\s*(--|#)/;

  // 如果触发了恒真式绕过
  if (alwaysTruePattern.test(lowerUsername) || alwaysTruePattern.test(lowerPassword)) {
    return {
      success: true,
      simulation: 'tautology',
      rows: MOCK_USERS, // 返回所有用户，模拟 SELECT * 绕过了 WHERE 过滤
      executedQuery: query
    };
  }

  // 如果触发了注释截断
  if (commentPattern.test(lowerUsername)) {
    const targetUser = username.split(/'|"| /)[0].trim();
    const found = MOCK_USERS.find(u => u.username.toLowerCase() === targetUser.toLowerCase());
    // 如果找到了对应的用户名，即使不输入密码也允许登录
    if (found || targetUser === "") {
      return {
        success: true,
        simulation: 'comment',
        rows: found ? [found] : [MOCK_USERS[0]],
        executedQuery: query
      };
    }
  }

  // --- 2. 模拟 SQL 语法错误检测 (只有在非攻击情况下才报错) ---
  const totalQuotes = (username.match(/'/g) || []).length + (password.match(/'/g) || []).length;
  if (totalQuotes % 2 !== 0) {
    return {
      success: false,
      rows: [],
      executedQuery: query,
      error: "SQL Syntax Error: 字符串后的引号未闭合。这通常意味着你的输入破坏了 SQL 结构！"
    };
  }

  // --- 3. 常规合法登录验证 ---
  // (演示环境默认密码均为 password123)
  const user = MOCK_USERS.find(u => u.username === username && password === 'password123');
  if (user) {
    return {
      success: true,
      simulation: 'normal',
      rows: [user],
      executedQuery: query
    };
  }

  return {
    success: false,
    rows: [],
    executedQuery: query,
    error: "Invalid credentials. Access Denied."
  };
};
