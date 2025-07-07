import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Types
export interface Template {
  template_id: string;
  name: string;
  supplier_name?: string;
  description?: string;
  supplier_aliases: string[];
  usage_count: number;
  success_rate: number;
  created_at?: string;
  updated_at?: string;
}

export interface TemplateCreate {
  template_id: string;
  name: string;
  supplier_name?: string;
  description?: string;
}

export interface ConversionJob {
  job_id: string;
  status: string;
  message: string;
  pdf_filename: string;
  template_used?: string;
  extraction_data?: any;
  ubl_xml?: string;
  confidence_scores?: Record<string, number>;
  created_at: string;
}

export interface ExtractionPreview {
  template_used: string;
  confidence_scores: Record<string, number>;
  extracted_fields: Record<string, any>;
  line_items: any[];
  raw_text_preview: string;
}

export interface TemplateStats {
  total_templates: number;
  suppliers_with_templates: number;
  average_success_rate: number;
  most_used_template?: string;
  most_used_template_usage: number;
}

export interface MLAnalysisResult {
  template_id: string;
  template_name: string;
  confidence_score: number;
  suggested_patterns: any[];
  field_mappings: Record<string, string>;
  supplier_patterns: any[];
}

export interface PatternAnalysisResult {
  suggested_patterns: any[];
  confidence_scores: number[];
  pattern_coverage: number;
  recommendations: string[];
}

// API Service
export class ApiService {
  // Templates
  async getTemplates(): Promise<Template[]> {
    const response = await api.get('/templates/');
    return response.data;
  }

  async getTemplate(templateId: string): Promise<Template> {
    const response = await api.get(`/templates/${templateId}`);
    return response.data;
  }

  async getTemplateDetails(templateId: string): Promise<any> {
    const response = await api.get(`/templates/${templateId}/details`);
    return response.data;
  }

  async createTemplate(template: TemplateCreate): Promise<Template> {
    const response = await api.post('/templates/', template);
    return response.data;
  }

  async updateTemplate(templateId: string, updates: Partial<TemplateCreate>): Promise<Template> {
    const response = await api.put(`/templates/${templateId}`, updates);
    return response.data;
  }

  async deleteTemplate(templateId: string): Promise<void> {
    await api.delete(`/templates/${templateId}`);
  }

  async getTemplateStats(): Promise<TemplateStats> {
    const response = await api.get('/templates/stats/overview');
    return response.data;
  }

  async addFieldRule(templateId: string, ruleData: any): Promise<void> {
    await api.post(`/templates/${templateId}/rules`, ruleData);
  }

  // Conversion
  async uploadAndConvert(
    file: File,
    templateId?: string,
    supplierHint?: string,
    previewOnly?: boolean
  ): Promise<ConversionJob> {
    const formData = new FormData();
    formData.append('file', file);
    if (templateId) formData.append('template_id', templateId);
    if (supplierHint) formData.append('supplier_hint', supplierHint);
    if (previewOnly) formData.append('preview_only', 'true');

    const response = await api.post('/conversion/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async previewExtraction(
    file: File,
    templateId?: string,
    supplierHint?: string
  ): Promise<ExtractionPreview> {
    const formData = new FormData();
    formData.append('file', file);
    if (templateId) formData.append('template_id', templateId);
    if (supplierHint) formData.append('supplier_hint', supplierHint);

    const response = await api.post('/conversion/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getConversionJob(jobId: string): Promise<ConversionJob> {
    const response = await api.get(`/conversion/jobs/${jobId}`);
    return response.data;
  }

  async getConversionJobs(limit = 50, offset = 0): Promise<ConversionJob[]> {
    const response = await api.get(`/conversion/jobs?limit=${limit}&offset=${offset}`);
    return response.data;
  }

  async deleteConversionJob(jobId: string): Promise<void> {
    await api.delete(`/conversion/jobs/${jobId}`);
  }

  async downloadUblXml(jobId: string): Promise<Blob> {
    const response = await api.get(`/conversion/jobs/${jobId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async downloadBatchZip(batchId: string, jobIds: string[]): Promise<Blob> {
    const response = await api.get(`/conversion/batch/${batchId}/download?job_ids=${jobIds.join(',')}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async batchConvert(
    files: File[],
    templateId?: string,
    supplierHint?: string
  ): Promise<{ batch_id: string; job_ids: string[]; message: string }> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (templateId) formData.append('template_id', templateId);
    if (supplierHint) formData.append('supplier_hint', supplierHint);

    const response = await api.post('/conversion/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // ML Features
  async generateTemplate(
    supplierName: string,
    templateId: string | undefined,
    sampleFiles: File[],
    confidenceThreshold: number = 0.5
  ): Promise<MLAnalysisResult> {
    console.log('API generateTemplate called with:', {
      supplierName,
      templateId,
      sampleFiles: sampleFiles.map(f => ({ name: f.name, size: f.size, type: f.type })),
      confidenceThreshold
    });

    const formData = new FormData();
    formData.append('supplier_name', supplierName);
    if (templateId) formData.append('template_id', templateId);
    formData.append('confidence_threshold', confidenceThreshold.toString());
    
    // Append all files
    sampleFiles.forEach(file => {
      console.log('Appending file:', file.name);
      formData.append('files', file);
    });

    console.log('FormData contents:');
    const entries = Array.from(formData.entries());
    entries.forEach(([key, value]) => {
      console.log(key, ':', value instanceof File ? `File: ${value.name}` : value);
    });

    const response = await api.post('/ml/generate-template', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async analyzePatterns(request: {
    text_samples: string[];
    field_type: string;
    existing_patterns?: string[];
  }): Promise<PatternAnalysisResult> {
    const response = await api.post('/ml/analyze-patterns', request);
    return response.data;
  }

  async predictConfidence(request: {
    template_id: string;
    text_content: string;
  }): Promise<{
    overall_confidence: number;
    field_confidences: Record<string, number>;
    quality_score: number;
    recommendations: string[];
  }> {
    const response = await api.post('/ml/predict-confidence', request);
    return response.data;
  }

  async analyzePdf(file: File, supplierName?: string): Promise<MLAnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (supplierName) formData.append('supplier_name', supplierName);

    const response = await api.post('/ml/analyze-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async trainModel(request: {
    training_data_path: string;
    model_type: string;
    hyperparameters?: Record<string, any>;
  }): Promise<{
    job_id: string;
    model_type: string;
    status: string;
    training_metrics?: Record<string, number>;
  }> {
    const response = await api.post('/ml/train-model', request);
    return response.data;
  }

  async getMLModels(): Promise<{
    models: Array<{
      name: string;
      status: string;
      version: string;
      description: string;
    }>;
  }> {
    const response = await api.get('/ml/models');
    return response.data;
  }

  async testTemplate(
    templateId: string,
    file: File
  ): Promise<{
    template_id: string;
    template_name: string;
    extracted_fields: Record<string, any>;
    extraction_details: Record<string, any>;
    confidence_scores: Record<string, number>;
    line_items: any[];
    raw_text_preview: string;
  }> {
    const formData = new FormData();
    formData.append('template_id', templateId);
    formData.append('file', file);

    const response = await api.post('/ml/test-template', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async improveTemplate(
    templateId: string,
    samplePdfs: string[]
  ): Promise<{
    template_id: string;
    improvements: string[];
    confidence_score: number;
    message: string;
  }> {
    const response = await api.post('/ml/improve-template', {
      template_id: templateId,
      sample_pdfs: samplePdfs,
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await api.get('/health');
    return response.data;
  }

  async getInfo(): Promise<{
    name: string;
    version: string;
    description: string;
    endpoints: Record<string, string>;
  }> {
    const response = await api.get('/info');
    return response.data;
  }
}

export const apiService = new ApiService();