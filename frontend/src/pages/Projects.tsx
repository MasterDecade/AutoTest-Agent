import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Modal, Space, Table, Typography, message } from 'antd'
import { PlusOutlined, CodeOutlined, AuditOutlined, BarChartOutlined, FileTextOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { createProject, getProjects } from '../api'

const { Title } = Typography

interface ProjectItem {
  id: string
  name: string
  language: string
  submission_count: number
  created_at: string
}

export default function Projects() {
  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const res = await getProjects()
      setProjects(res.data)
    } catch {
      message.error('加载项目列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      const res = await createProject({
        name: values.name,
        description: values.description,
        language: values.language || undefined,
      })
      message.success('项目已保存到数据库')
      setOpen(false)
      form.resetFields()
      await fetchProjects()
      // Navigate to project content definition page
      navigate(`/projects/${res.data.id}/content`)
    } catch (e: any) {
      if (e.response) {
        message.error(e.response?.data?.detail || '保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { title: '项目名称', dataIndex: 'name', key: 'name' },
    { title: '语言', dataIndex: 'language', key: 'language', width: 100 },
    { title: '提交数', dataIndex: 'submission_count', key: 'submission_count', width: 80 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    {
      title: '操作', key: 'actions', width: 360,
      render: (_: any, record: ProjectItem) => (
        <Space wrap>
          <Button icon={<FileTextOutlined />} size="small"
            onClick={() => navigate(`/projects/${record.id}/content`)}>
            项目内容
          </Button>
          <Button icon={<AuditOutlined />} size="small"
            onClick={() => navigate(`/projects/${record.id}/review`)}>
            审核计划
          </Button>
          <Button icon={<CodeOutlined />} size="small"
            onClick={() => navigate(`/projects/${record.id}/submit`)}>
            提交代码
          </Button>
          <Button icon={<BarChartOutlined />} size="small"
            onClick={() => navigate(`/projects/${record.id}/compare`)}>
            评分对比
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>项目管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>创建项目</Button>
      </div>

      <Card>
        <Table dataSource={projects} columns={columns} rowKey="id" loading={loading}
          locale={{ emptyText: '暂无项目，点击右上角创建' }} />
      </Card>

      <Modal open={open} title="创建新项目" onCancel={() => { setOpen(false); form.resetFields() }}
        onOk={handleSave} confirmLoading={saving} okText="保存到数据库">
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如：Python 期末作业" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea rows={3} placeholder="简要描述项目内容和要求" />
          </Form.Item>
          <Form.Item name="language" label="编程语言">
            <Input placeholder="python/cpp/java (留空自动检测)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
