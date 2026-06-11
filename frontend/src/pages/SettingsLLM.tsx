import { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Modal, Space, Table, Typography, Tag, message } from 'antd'
import { PlusOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons'
import { getLLMProviders, addLLMProvider, testLLMProvider, removeLLMProvider } from '../api'

const { Title } = Typography

interface Provider {
  provider_type: string
  model_name: string
  api_base: string
  priority: number
  healthy?: boolean
}

export default function SettingsLLM() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()
  const [testing, setTesting] = useState(false)

  const refresh = async () => {
    try {
      const res = await getLLMProviders()
      setProviders(res.data.providers || [])
    } catch { /* noop */ }
  }

  useEffect(() => { refresh() }, [])

  const handleAdd = async (values: any) => {
    try {
      await addLLMProvider(values)
      message.success('提供商已添加')
      setOpen(false)
      form.resetFields()
      refresh()
    } catch (e: any) { message.error(e.response?.data?.detail || '添加失败') }
  }

  const handleDelete = async (type: string, model: string) => {
    try {
      await removeLLMProvider(type, model)
      message.success('已删除')
      refresh()
    } catch { message.error('删除失败') }
  }

  const handleTest = async (type: string, model: string) => {
    setTesting(true)
    try {
      await testLLMProvider({ provider_type: type, model_name: model })
      message.success('连接成功')
    } catch { message.error('连接失败') }
    finally { setTesting(false) }
  }

  const columns = [
    { title: '提供商', dataIndex: 'provider_type', key: 'provider_type' },
    { title: '模型', dataIndex: 'model_name', key: 'model_name' },
    {
      title: '状态', key: 'status',
      render: (_: any, r: Provider) => <Tag color={r.healthy !== false ? 'green' : 'red'}>{r.healthy !== false ? '在线' : '离线'}</Tag>,
    },
    {
      title: '操作', key: 'actions',
      render: (_: any, r: Provider) => (
        <Space>
          <Button icon={<ApiOutlined />} size="small" loading={testing} onClick={() => handleTest(r.provider_type, r.model_name)}>
            测试
          </Button>
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDelete(r.provider_type, r.model_name)}>
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>LLM 提供商配置</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>添加 API Key</Button>
      </div>

      <Card>
        <Table dataSource={providers} columns={columns} rowKey={(r) => `${r.provider_type}:${r.model_name}`} locale={{ emptyText: '尚未配置 LLM 提供商' }} />
      </Card>

      <Modal open={open} title="添加 LLM 提供商" onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleAdd}>
          <Form.Item name="provider_type" label="提供商" rules={[{ required: true }]}>
            <Input placeholder="openai / qwen / deepseek / zhipuai" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}>
            <Input placeholder="gpt-4o / qwen-max / deepseek-chat" />
          </Form.Item>
          <Form.Item name="api_base" label="API Base URL (可选)">
            <Input placeholder="https://api.openai.com" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}