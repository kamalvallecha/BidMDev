import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, Form, Select, message } from 'antd';
import PartnerForm from './PartnerForm';
import axios from '../../api/axios';

const { Option } = Select;

const specializations = [
    'B2B',
    'B2C',
    'HC - HCP',
    'HC - Patient',
    'Custom'
];

// List of all countries
const countries = [
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
    'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 
    'Botswana', 'Brazil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi',
    'India', 'USA', 'UK', 'Canada', 'Australia', 'Germany', 'France', 'Japan', 'China'
    // Add more countries as needed
];

const Partners = () => {
  const [partners, setPartners] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [currentPartner, setCurrentPartner] = useState(null);
  const [editForm] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchPartners = async () => {
    try {
      const response = await axios.get('/api/partners');
      setPartners(response.data);
    } catch (error) {
      console.error('Error fetching partners:', error);
    }
  };

  useEffect(() => {
    fetchPartners();
  }, []);

  const columns = [
    {
      title: 'Partner ID',
      dataIndex: 'partner_id',
      key: 'partner_id',
    },
    {
      title: 'Partner Name',
      dataIndex: 'partner_name',
      key: 'partner_name',
    },
    {
      title: 'Contact Person',
      dataIndex: 'contact_person',
      key: 'contact_person',
    },
    {
      title: 'Contact Email',
      dataIndex: 'contact_email',
      key: 'contact_email',
    },
    {
      title: 'Specialized',
      dataIndex: 'specialized',
      key: 'specialized',
      render: (specialized) => Array.isArray(specialized) ? specialized.join(', ') : specialized
    },
    {
      title: 'Geographic Coverage',
      dataIndex: 'geographic_coverage',
      key: 'geographic_coverage',
      render: (coverage) => Array.isArray(coverage) ? coverage.join(', ') : coverage
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <>
          <Button type="link" onClick={() => handleEdit(record)}>Edit</Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>Delete</Button>
        </>
      ),
    },
  ];

  const handleAddPartner = () => {
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  const handleFormSubmit = async (values) => {
    await fetchPartners();
    setIsModalVisible(false);
  };

  const handleEdit = (record) => {
    setCurrentPartner(record);
    editForm.setFieldsValue({
      partner_name: record.partner_name,
      contact_person: record.contact_person,
      contact_email: record.contact_email,
      contact_phone: record.contact_phone,
      website: record.website,
      company_address: record.company_address,
      specialized: record.specialized,
      geographic_coverage: record.geographic_coverage
    });
    setIsEditModalVisible(true);
  };

  const handleEditCancel = () => {
    setIsEditModalVisible(false);
    setCurrentPartner(null);
  };

  const handleEditSubmit = async (values) => {
    if (!currentPartner) return;
    
    try {
      setLoading(true);
      const response = await axios.put(`/api/partners/${currentPartner.id}`, values);
      if (response.status === 200) {
        message.success('Partner updated successfully');
        fetchPartners();
        setIsEditModalVisible(false);
        setCurrentPartner(null);
      }
    } catch (error) {
      console.error('Error updating partner:', error);
      message.error('Failed to update partner: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (partnerId) => {
    if (window.confirm('Are you sure you want to delete this partner?')) {
      try {
        const response = await axios.delete(`/api/partners/${partnerId}`);
        if (response.status === 200) {
          message.success('Partner deleted successfully');
          fetchPartners();
        }
      } catch (error) {
        console.error('Error deleting partner:', error);
        message.error('Failed to delete partner: ' + (error.response?.data?.error || error.message));
      }
    }
  };

  const filteredPartners = partners.filter(partner => 
    partner.partner_name?.toLowerCase().includes(searchText.toLowerCase()) ||
    partner.partner_id?.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '16px' 
      }}>
        <h2 style={{ margin: 0 }}>Partner List</h2>
        <div style={{ display: 'flex', gap: '16px' }}>
          <Input.Search
            placeholder="Search partners..."
            style={{ width: 300 }}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Button type="primary" onClick={handleAddPartner}>
            ADD PARTNER
          </Button>
        </div>
      </div>

      <Table
        columns={columns}
        dataSource={filteredPartners}
        rowKey="id"
        bordered
        style={{ backgroundColor: 'white' }}
      />

      <Modal
        title="Add New Partner"
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        width={800}
      >
        <PartnerForm
          onSuccess={handleFormSubmit}
          onCancel={handleModalCancel}
        />
      </Modal>

      <Modal
        title="Edit Partner"
        open={isEditModalVisible}
        onCancel={handleEditCancel}
        footer={null}
        width={800}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item
            name="partner_name"
            label="Partner Name"
            rules={[{ required: true, message: 'Please enter partner name' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="contact_person"
            label="Contact Person"
            rules={[{ required: true, message: 'Please enter contact person' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="contact_email"
            label="Contact Email"
            rules={[
              { required: true, message: 'Please enter contact email' },
              { type: 'email', message: 'Please enter a valid email' }
            ]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="contact_phone"
            label="Contact Phone"
            rules={[{ required: true, message: 'Please enter contact phone' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="website"
            label="Website"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="company_address"
            label="Company Address"
            rules={[{ required: true, message: 'Please enter company address' }]}
          >
            <Input.TextArea rows={2} />
          </Form.Item>
          
          <Form.Item
            name="specialized"
            label="Specialized"
            rules={[{ required: true, message: 'Please select specializations' }]}
          >
            <Select
              mode="multiple"
              placeholder="Select specializations"
              style={{ width: '100%' }}
            >
              {specializations.map(spec => (
                <Option key={spec} value={spec}>{spec}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="geographic_coverage"
            label="Geographic Coverage"
            rules={[{ required: true, message: 'Please select countries' }]}
          >
            <Select
              mode="multiple"
              placeholder="Select countries"
              style={{ width: '100%' }}
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {countries.map(country => (
                <Option key={country} value={country}>{country}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '24px' }}>
            <Button onClick={handleEditCancel}>
              Cancel
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              Update Partner
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default Partners; 