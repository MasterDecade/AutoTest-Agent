import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Button, Card, Form, Input, Select, Space, Typography, Upload, message, Tag,
  Descriptions, Progress, List, Divider, Alert,
} from 'antd'
import {
  UploadOutlined, CodeOutlined, PlayCircleOutlined, InboxOutlined,
  FileZipOutlined, FileTextOutlined,
} from '@ant-design/icons'
import { generateTests, runTests, generateAndRun, uploadSubmission, getSubmissions } from '../api'

const { Title, Text } = Typography
const { Dragger } = Upload

interface UploadedFile {
  file_name: string
  file_path: string
  language: string | null
  size_bytes: number
}

interface UploadResult {
  submission_id: string
  project_id: string
  submitter_name: string | null
  files: UploadedFile[]
  detected_language: string | null
  total_files: number
  status: string
}

export default function SubmitCode() {
  const { projectId } = useParams()
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [submitterName, setSubmitterName] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [language, setLanguage] = useState('')

  // Handle file upload (single or multiple)
  const handleUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files)
    if (fileArray.length === 0) {
      message.warning('请选择文件')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      fileArray.forEach(file => {
        formData.append('files', file)
      })
      if (submitterName.trim()) {
        formData.append('submitter_name', submitterName.trim())
      }

      const res = await uploadSubmission(projectId!, formData)
      setUploadResult(res.data)
      setUploadProgress(100)
      if (res.data.detected_language) {
        setLanguage(res.data.detected_language)
      }
      message.success(`上传成功：${res.data.total_files} 个文件，语言: ${res.data.detected_language || '自动检测'}`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  // Run tests on uploaded code
  const handleRunTests = async () => {
    if (!uploadResult) {
      message.warning('请先上传代码文件')
      return
    }
    setTesting(true)
    try {
      // Use a placeholder code to trigger test generation
      const detectedLang = uploadResult.detected_language || language || 'python'
      const fileNames = uploadResult.files.map(f => f.file_path).join(', ')
      const placeholderCode = `# Project: ${projectId}\n# Files: ${fileNames}\n# Submit by: ${submitterName || 'anonymous'}`

      const res = await generateAndRun({
        code: placeholderCode,
        language: detectedLang,
        num_cases: 5,
      })
      setTestResult(res.data)
      message.success('测试执行完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '测试执行失败')
    } finally {
      setTesting(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div>
      <Title level={3}>
        提交代码
        {projectId && <Tag color="blue" style={{ marginLeft: 8 }}>项目: {projectId}</Tag>}
      </Title>

      {/* Upload Section */}
      <Card title="📤 上传代码文件" style={{ marginBottom: 16 }}>
        <Alert
          type="info"
          message="支持上传单个代码文件或包含多个文件的 zip 压缩包"
          description="支持 .py, .cpp, .c, .java, .go, .rs, .js, .ts 等代码文件。zip 压缩包将自动解压并保持目录结构。"
          style={{ marginBottom: 16 }}
          showIcon
        />

        <Form.Item label="提交者名称">
          <Input
            placeholder="输入提交者姓名（可选）"
            value={submitterName}
            onChange={e => setSubmitterName(e.target.value)}
            style={{ maxWidth: 300 }}
          />
        </Form.Item>

        <div style={{ marginBottom: 16 }}>
          <Space>
            <Select
              placeholder="指定语言（可选）"
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
            <Text type="secondary">留空则自动检测</Text>
          </Space>
        </div>

        <Dragger
          accept=".py,.cpp,.c,.cc,.cxx,.h,.hpp,.java,.go,.rs,.js,.jsx,.ts,.tsx,.rb,.cs,.php,.kt,.sh,.zip"
          multiple
          beforeUpload={(file, fileList) => {
            handleUpload(fileList)
            return false // Prevent default upload
          }}
          disabled={uploading}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个代码文件、多个文件，或 ZIP 压缩包（批量提交请打包每个提交者为单独 zip）
          </p>
        </Dragger>

        {uploading && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={uploadProgress} status="active" />
            <Text type="secondary">正在上传并分析文件...</Text>
          </div>
        )}
      </Card>

      {/* Upload Result */}
      {uploadResult && (
        <Card title="📋 上传结果" style={{ marginBottom: 16 }}>
          <Descriptions column={3} size="small">
            <Descriptions.Item label="提交ID">{uploadResult.submission_id}</Descriptions.Item>
            <Descriptions.Item label="检测语言">
              <Tag color="blue">{uploadResult.detected_language || '未检测'}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="文件数">{uploadResult.total_files}</Descriptions.Item>
            <Descriptions.Item label="提交者">{uploadResult.submitter_name || '匿名'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color="green">{uploadResult.status}</Tag>
            </Descriptions.Item>
          </Descriptions>

          <Divider orientation="left">文件列表</Divider>
          <List
            size="small"
            dataSource={uploadResult.files}
            renderItem={(item: UploadedFile) => (
              <List.Item>
                <Space>
                  {item.file_path.endsWith('.zip') ? <FileZipOutlined /> : <FileTextOutlined />}
                  <Text>{item.file_path}</Text>
                  <Tag>{item.language || '未知'}</Tag>
                  <Text type="secondary">{formatSize(item.size_bytes)}</Text>
                </Space>
              </List.Item>
            )}
          />

          <Divider />
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={testing}
              onClick={handleRunTests}
              size="large"
            >
              执行测试
            </Button>
            <Button
              icon={<UploadOutlined />}
              onClick={() => {
                setUploadResult(null)
                setUploadProgress(0)
                setTestResult(null)
              }}
            >
              重新上传
            </Button>
          </Space>
        </Card>
      )}

      {/* Test Results */}
      {testResult && (
        <Card title="🧪 测试执行结果">
          <Descriptions column={4} size="small">
            <Descriptions.Item label="总用例">{testResult.total}</Descriptions.Item>
            <Descriptions.Item label="通过">
              <span style={{ color: '#52c41a' }}>{testResult.passed}</span>
            </Descriptions.Item>
            <Descriptions.Item label="失败">
              <span style={{ color: '#ff4d4f' }}>{testResult.failed}</span>
            </Descriptions.Item>
            <Descriptions.Item label="错误">{testResult.errors}</Descriptions.Item>
            <Descriptions.Item label="通过率">{testResult.pass_rate}%</Descriptions.Item>
            <Descriptions.Item label="覆盖率">{testResult.coverage}%</Descriptions.Item>
            <Descriptions.Item label="耗时">{testResult.duration_ms}ms</Descriptions.Item>
            <Descriptions.Item label="超时">{testResult.timed_out ? '是' : '否'}</Descriptions.Item>
          </Descriptions>
          {testResult.stdout && (
            <pre style={{
              background: '#f5f5f5', padding: 12, borderRadius: 4,
              maxHeight: 300, overflow: 'auto', marginTop: 8, fontSize: 12,
            }}>
              {testResult.stdout}
            </pre>
          )}
          {testResult.stderr && (
            <Alert type="error" message="错误输出" description={
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12 }}>{testResult.stderr}</pre>
            } style={{ marginTop: 8 }} />
          )}
        </Card>
      )}
    </div>
  )
}
