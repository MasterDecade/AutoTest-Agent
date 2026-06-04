import { useState } from 'react'
import { Button, Card, Form, Input, Modal, Space, Table, Typography, message } from 'antd'
import { PlusOutlined, CodeOutlined, AuditOutlined, BarChartOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

interface ProjectItem {
  id: string
  name: string
  language: string
  submissions: number
}

export default function Projects() {
  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  const handleCreate = (values: any) => {
    const newProject: ProjectItem = {
      id: Date.now().toString(),
      name: values.name,
      language: values.language || 'auto',
      submissions: 0,
    }
    setProjects([...projects, newProject])
    setOpen(false)
    form.resetFields()
    message.success('项目创建成功')
  }

  const columns = [
    { title: '项目名称', dataIndex: 'name', key: 'name' },
    { title: '语言', dataIndex: 'language', key: 'language', width: 100 },
    { title: '提交数', dataIndex: 'submissions', key: 'submissions', width: 80 },
    {
      title: '操作', key: 'actions', width: 280,
      render: (_: any, record: ProjectItem) => (
        <Space>
          <Button icon={<CodeOutlined />} size="small" onClick={() => navigate(`/projects/${record.id}/submit`)}>
            提交代码
          </Button>
          <Button icon={<AuditOutlined />} size="small" onClick={() => navigate(`/projects/${record.id}/review`)}>
            审核计划
          </Button>
          <Button icon={<BarChartOutlined />} size="small" onClick={() => navigate(`/projects/${record.id}/compare`)}>
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
        <Table dataSource={projects} columns={columns} rowKey="id" locale={{ emptyText: '暂无项目，点击右上角创建' }} />
      </Card>

      <Modal open={open} title="创建新项目" onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如：Python 期末作业" />
          </Form.Item>
          <Form.Item name="language" label="编程语言">
            <Input placeholder="python/cpp/java (留空自动检测)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}