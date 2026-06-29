import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Card, Form, Input, Upload, Typography, message, Space, Spin, Tag, Divider, List, Descriptions,
} from 'antd'
import {
  UploadOutlined, FileTextOutlined, RobotOutlined, AuditOutlined, InboxOutlined,
} from '@ant-design/icons'
import { getProject, uploadDocument, generatePlan } from '../api'

const { Title, Text } = Typography
const { TextArea } = Input
const { Dragger } = Upload

interface AnalyzedDoc {
  file_name: string
  text_preview: string
  text_length: number
  analysis: {
    doc_category: string
    key_requirements: string[]
    test_criteria: string[]
    scoring_rules: Array<{ dimension: string; weight: number; description: string }>
    code_style_rules: string[]
    referenced_functions: string[]
    edge_cases: string[]
    environment_requirements: Record<string, any>
    uncertainty_notes: string[]
  } | null
}

export default function ProjectContent() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const [project, setProject] = useState<any>(null)
  const [textInput, setTextInput] = useState('')
  const [uploadedDocs, setUploadedDocs] = useState<AnalyzedDoc[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [planGenerated, setPlanGenerated] = useState(false)

  useEffect(() => {
    if (projectId) {
      getProject(projectId).then(res => setProject(res.data)).catch(() => message.error('加载项目失败'))
    }
  }, [projectId])

  // Upload file and analyze
  const handleFileUpload = async (file: File) => {
    setAnalyzing(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await uploadDocument(formData)
      setUploadedDocs(prev => [...prev, res.data])
      message.success(`文件 "${file.name}" 分析完成`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '文件分析失败')
    } finally {
      setAnalyzing(false)
    }
    return false // Prevent default upload
  }

  // Analyze text input
  const handleAnalyzeText = async () => {
    if (!textInput.trim()) {
      message.warning('请输入项目要求文本')
      return
    }
    setAnalyzing(true)
    try {
      const { default: api } = await import('../api')
      const res = await api.post('/documents/analyze-text', null, {
        params: { text: textInput, project_context: project?.description || '' },
      })
      setUploadedDocs(prev => [...prev, res.data])
      message.success('文本分析完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '文本分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  // Generate inspection plan from analyzed docs
  const handleGeneratePlan = async () => {
    if (uploadedDocs.length === 0) {
      message.warning('请先上传文档或输入文本并分析')
      return
    }
    setGenerating(true)
    try {
      const docTexts = uploadedDocs
        .filter(d => d.analysis?.key_requirements)
        .map(d => d.text_preview || '')

      const sampleCode = uploadedDocs
        .flatMap(d => d.analysis?.referenced_functions || [])
        .join('\n') || '// Sample code placeholder'

      const res = await generatePlan({
        project_id: projectId,
        project_name: project?.name || 'Unknown Project',
        code: sampleCode || 'def placeholder(): pass',
        language: project?.language || 'python',
        document_texts: docTexts.length > 0 ? docTexts : undefined,
      })
      message.success('检测计划已生成，即将跳转到审核页面')
      setPlanGenerated(true)
      // Navigate to review page with plan_id
      setTimeout(() => {
        navigate(`/projects/${projectId}/review?plan_id=${res.data.plan_id}`)
      }, 800)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '计划生成失败')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div>
      <Title level={3}>
        项目内容定义
        {project && <Tag color="blue" style={{ marginLeft: 8 }}>{project.name}</Tag>}
      </Title>

      {/* Project Info */}
      {project && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Descriptions column={3} size="small">
            <Descriptions.Item label="项目名称">{project.name}</Descriptions.Item>
            <Descriptions.Item label="语言">{project.language || '自动检测'}</Descriptions.Item>
            <Descriptions.Item label="描述">{project.description || '无'}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* Text Input Section */}
      <Card title="📝 文本输入" style={{ marginBottom: 16 }}>
        <Text type="secondary">
          在此填写项目要求、格式约束、评分标准等详细信息，系统将自动提取关键需求。
        </Text>
        <TextArea
          rows={6}
          placeholder={'项目要求：\n1. 实现一个计算器功能，支持加减乘除\n2. 输入为两个整数，输出为计算结果\n\n格式约束：\n1. 必须使用面向对象设计\n2. 函数命名使用lower_snake_case\n\n评分标准：\n1. 功能正确性 40%\n2. 代码风格 20%\n3. 异常处理 20%\n4. 测试覆盖率 20%'}
          value={textInput}
          onChange={e => setTextInput(e.target.value)}
          style={{ marginTop: 8, marginBottom: 8 }}
        />
        <Button
          icon={<RobotOutlined />}
          loading={analyzing}
          onClick={handleAnalyzeText}
        >
          分析文本内容
        </Button>
      </Card>

      {/* File Upload Section */}
      <Card title="📎 文件上传" style={{ marginBottom: 16 }}>
        <Text type="secondary">支持 PDF、Markdown、DOCX、TXT 格式，上传后自动提取文本并分析。</Text>
        <div style={{ marginTop: 12 }}>
          <Dragger
            accept=".pdf,.docx,.md,.txt,.html,.rst"
            beforeUpload={handleFileUpload}
            showUploadList={false}
            disabled={analyzing}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">支持 PDF / DOCX / Markdown / TXT</p>
          </Dragger>
        </div>
      </Card>

      {/* Analyzed Documents */}
      {uploadedDocs.length > 0 && (
        <Card title="📊 分析结果" style={{ marginBottom: 16 }}>
          {uploadedDocs.map((doc, idx) => (
            <div key={idx} style={{ marginBottom: idx < uploadedDocs.length - 1 ? 16 : 0 }}>
              <Text strong>{doc.file_name}</Text>
              <Tag style={{ marginLeft: 8 }}>
                {doc.analysis?.doc_category || '未分类'}
              </Tag>

              <Divider style={{ margin: '8px 0' }} />

              {doc.analysis?.key_requirements && doc.analysis.key_requirements.length > 0 && (
                <>
                  <Text strong>关键需求：</Text>
                  <List size="small" dataSource={doc.analysis.key_requirements}
                    renderItem={(item: string) => <List.Item>• {item}</List.Item>} />
                </>
              )}

              {doc.analysis?.test_criteria && doc.analysis.test_criteria.length > 0 && (
                <>
                  <Text strong>测试标准：</Text>
                  <List size="small" dataSource={doc.analysis.test_criteria}
                    renderItem={(item: string) => <List.Item>✓ {item}</List.Item>} />
                </>
              )}

              {doc.analysis?.scoring_rules && doc.analysis.scoring_rules.length > 0 && (
                <>
                  <Text strong>评分规则：</Text>
                  <List size="small" dataSource={doc.analysis.scoring_rules}
                    renderItem={(item: any) => (
                      <List.Item>
                        📊 {item.dimension} — 权重: {item.weight}%
                        {item.description && ` (${item.description})`}
                      </List.Item>
                    )} />
                </>
              )}

              {doc.analysis?.uncertainty_notes && doc.analysis.uncertainty_notes.length > 0 && (
                <>
                  <Text strong style={{ color: '#faad14' }}>⚠ 不确定项：</Text>
                  <List size="small" dataSource={doc.analysis.uncertainty_notes}
                    renderItem={(item: string) => <List.Item style={{ color: '#faad14' }}>• {item}</List.Item>} />
                </>
              )}

              {idx < uploadedDocs.length - 1 && <Divider />}
            </div>
          ))}

          <Divider />

          <Space>
            <Button
              type="primary"
              size="large"
              icon={<AuditOutlined />}
              loading={generating}
              onClick={handleGeneratePlan}
              disabled={planGenerated}
            >
              生成检测计划
            </Button>
            {planGenerated && (
              <Button onClick={() => navigate(`/projects/${projectId}/review`)}>
                前往审核页面
              </Button>
            )}
          </Space>
        </Card>
      )}

      {analyzing && (
        <Card>
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin size="large" />
            <p style={{ marginTop: 12 }}>正在分析文档内容，请稍候...</p>
          </div>
        </Card>
      )}
    </div>
  )
}
