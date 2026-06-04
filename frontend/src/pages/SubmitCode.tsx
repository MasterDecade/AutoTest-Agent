import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, Card, Form, Input, Select, Space, Typography, Upload, message, Spin, Descriptions, Tag } from 'antd'
import { UploadOutlined, CodeOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { generateTests, runTests, generateAndRun, analyzeCode } from '../api'

const { Title } = Typography
const { TextArea } = Input

export default function SubmitCode() {
  const { projectId } = useParams()
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)

  const handleAnalyze = async () => {
    if (!code.trim()) { message.warning('请输入代码'); return }
    setLoading(true)
    try {
      const res = await analyzeCode({ code, language: language || undefined })
      setAnalysis(res.data)
      message.success('代码分析完成')
    } catch (e: any) { message.error(e.response?.data?.detail || '分析失败') }
    finally { setLoading(false) }
  }

  const handleTest = async () => {
    if (!code.trim()) { message.warning('请输入代码'); return }
    setLoading(true)
    try {
      const res = await generateAndRun({ code, language: language || 'python', num_cases: 5 })
      setResult(res.data)
      message.success('测试完成')
    } catch (e: any) { message.error(e.response?.data?.detail || '测试失败') }
    finally { setLoading(false) }
  }

  return (
    <div>
      <Title level={3}>提交代码 {projectId && <Tag color="blue">项目: {projectId}</Tag>}</Title>

      <Card style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <Space>
            <Select
              placeholder="语言 (自动检测)"
              allowClear
              style={{ width: 160 }}
              value={language || undefined}
              onChange={setLanguage}
              options={[
                { label: 'Python', value: 'python' },
                { label: 'C++', value: 'cpp' },
                { label: 'C', value: 'c' },
                { label: 'Java', value: 'java' },
              ]}
            />
            <Button icon={<CodeOutlined />} loading={loading} onClick={handleAnalyze}>分析代码</Button>
            <Button type="primary" icon={<PlayCircleOutlined />} loading={loading} onClick={handleTest}>生成并运行测试</Button>
          </Space>
        </div>
        <TextArea rows={12} placeholder="在此粘贴源代码..." value={code} onChange={e => setCode(e.target.value)} />
      </Card>

      {analysis && (
        <Card title="📊 代码分析结果" style={{ marginBottom: 16 }}>
          <Descriptions column={3}>
            <Descriptions.Item label="语言">{analysis.language}</Descriptions.Item>
            <Descriptions.Item label="语法评分">{analysis.syntax_score}</Descriptions.Item>
            <Descriptions.Item label="风格评分">{analysis.style_score}</Descriptions.Item>
          </Descriptions>
          {analysis.summary && <p>{analysis.summary}</p>}
        </Card>
      )}

      {result && (
        <Card title="🧪 测试结果">
          <Descriptions column={4}>
            <Descriptions.Item label="总用例">{result.total}</Descriptions.Item>
            <Descriptions.Item label="通过"><span style={{ color: '#52c41a' }}>{result.passed}</span></Descriptions.Item>
            <Descriptions.Item label="失败"><span style={{ color: '#ff4d4f' }}>{result.failed}</span></Descriptions.Item>
            <Descriptions.Item label="通过率">{result.pass_rate}%</Descriptions.Item>
            <Descriptions.Item label="覆盖率">{result.coverage}%</Descriptions.Item>
            <Descriptions.Item label="耗时">{result.duration_ms}ms</Descriptions.Item>
          </Descriptions>
          {result.stdout && <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, maxHeight: 300, overflow: 'auto' }}>{result.stdout}</pre>}
        </Card>
      )}
    </div>
  )
}