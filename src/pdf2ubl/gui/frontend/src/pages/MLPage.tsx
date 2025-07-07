import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  SmartToy,
  Upload,
  CloudUpload,
  ExpandMore,
  AutoFixHigh,
  Analytics,
  TrendingUp,
  CheckCircle,
  Warning,
  Error,
  Psychology,
  Biotech,
  Insights,
  ModelTraining,
  FileUpload,
  Add,
  Delete,
  Save,
  PlayArrow,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery } from 'react-query';
import { useSnackbar } from 'notistack';

import { apiService } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ml-tabpanel-${index}`}
      aria-labelledby={`ml-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MLPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [tabValue, setTabValue] = useState(0);
  
  // Auto-Template Generation state
  const [supplierName, setSupplierName] = useState('');
  const [templateId, setTemplateId] = useState('');
  const [sampleFiles, setSampleFiles] = useState<File[]>([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
  const [generationResult, setGenerationResult] = useState<any>(null);
  const [showTemplatePreview, setShowTemplatePreview] = useState(false);
  
  // Pattern Analysis state
  const [textSamples, setTextSamples] = useState<string[]>(['']);
  const [fieldType, setFieldType] = useState('text');
  const [existingPatterns, setExistingPatterns] = useState<string[]>(['']);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  
  // Template Improvement state
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [improvementFiles, setImprovementFiles] = useState<File[]>([]);
  const [improvementResult, setImprovementResult] = useState<any>(null);
  
  // Confidence Prediction state
  const [predictionTemplate, setPredictionTemplate] = useState('');
  const [predictionText, setPredictionText] = useState('');
  const [predictionResult, setPredictionResult] = useState<any>(null);
  
  // Single PDF Analysis state
  const [analysisFile, setAnalysisFile] = useState<File | null>(null);
  const [analysisSupplier, setAnalysisSupplier] = useState('');
  const [pdfAnalysisResult, setPdfAnalysisResult] = useState<any>(null);
  
  // Template Testing state
  const [templateTestResult, setTemplateTestResult] = useState<any>(null);

  // Fetch templates for dropdowns
  const { data: templates = [] } = useQuery('templates', apiService.getTemplates);
  const { data: mlModels } = useQuery('mlModels', apiService.getMLModels);

  // Mutations
  const generateTemplateMutation = useMutation(
    ({ supplierName, templateId, sampleFiles, confidenceThreshold }: {
      supplierName: string;
      templateId?: string;
      sampleFiles: File[];
      confidenceThreshold: number;
    }) => apiService.generateTemplate(supplierName, templateId, sampleFiles, confidenceThreshold),
    {
      onSuccess: (result) => {
        setGenerationResult(result);
        enqueueSnackbar('Template generation completed!', { variant: 'success' });
      },
      onError: (error: any) => {
        const errorMessage = error.response?.data?.detail 
          ? (Array.isArray(error.response.data.detail) 
              ? error.response.data.detail.map((e: any) => e.msg).join(', ')
              : error.response.data.detail)
          : error.message;
        enqueueSnackbar(`Error: ${errorMessage}`, { variant: 'error' });
      },
    }
  );

  const analyzePatternsMutation = useMutation(apiService.analyzePatterns, {
    onSuccess: (result) => {
      setAnalysisResult(result);
      enqueueSnackbar('Pattern analysis completed!', { variant: 'success' });
    },
    onError: (error: any) => {
      enqueueSnackbar(`Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
    },
  });

  const analyzePdfMutation = useMutation(
    ({ file, supplierName }: { file: File; supplierName?: string }) => 
      apiService.analyzePdf(file, supplierName),
    {
      onSuccess: (result) => {
        setPdfAnalysisResult(result);
        enqueueSnackbar('PDF analysis completed!', { variant: 'success' });
      },
      onError: (error: any) => {
        enqueueSnackbar(`Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  const predictConfidenceMutation = useMutation(apiService.predictConfidence, {
    onSuccess: (result) => {
      setPredictionResult(result);
      enqueueSnackbar('Confidence prediction completed!', { variant: 'success' });
    },
    onError: (error: any) => {
      enqueueSnackbar(`Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
    },
  });

  const testTemplateMutation = useMutation(
    ({ templateId, file }: { templateId: string; file: File }) => 
      apiService.testTemplate(templateId, file),
    {
      onSuccess: (result) => {
        setTemplateTestResult(result);
        enqueueSnackbar('Template test completed!', { variant: 'success' });
      },
      onError: (error: any) => {
        enqueueSnackbar(`Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  // File drop handlers
  const onDropSamples = (acceptedFiles: File[]) => {
    setSampleFiles(prev => [...prev, ...acceptedFiles]);
  };

  const onDropImprovement = (acceptedFiles: File[]) => {
    setImprovementFiles(prev => [...prev, ...acceptedFiles]);
  };

  const onDropAnalysis = (acceptedFiles: File[]) => {
    if (acceptedFiles[0]) {
      setAnalysisFile(acceptedFiles[0]);
    }
  };

  const { getRootProps: getSampleProps, getInputProps: getSampleInputs } = useDropzone({
    onDrop: onDropSamples,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  const { getRootProps: getImprovementProps, getInputProps: getImprovementInputs } = useDropzone({
    onDrop: onDropImprovement,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  const { getRootProps: getAnalysisProps, getInputProps: getAnalysisInputs } = useDropzone({
    onDrop: onDropAnalysis,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
  });

  // Handlers
  const handleGenerateTemplate = async () => {
    if (!supplierName.trim()) {
      enqueueSnackbar('Supplier name is required', { variant: 'error' });
      return;
    }
    
    if (sampleFiles.length === 0) {
      enqueueSnackbar('At least one sample PDF is required', { variant: 'error' });
      return;
    }
    
    console.log('Generating template with:', {
      supplierName,
      templateId,
      sampleFiles: sampleFiles.map(f => f.name),
      confidenceThreshold: 0.5
    });
    
    generateTemplateMutation.mutate({
      supplierName: supplierName,
      templateId: templateId || undefined,
      sampleFiles: sampleFiles,
      confidenceThreshold: confidenceThreshold,
    });
  };

  const handleAnalyzePatterns = () => {
    if (textSamples.filter(t => t.trim()).length === 0) {
      enqueueSnackbar('At least one text sample is required', { variant: 'error' });
      return;
    }

    analyzePatternsMutation.mutate({
      text_samples: textSamples.filter(t => t.trim()),
      field_type: fieldType,
      existing_patterns: existingPatterns.filter(p => p.trim()),
    });
  };

  const handleAnalyzePdf = () => {
    if (!analysisFile) {
      enqueueSnackbar('Please select a PDF file', { variant: 'error' });
      return;
    }

    analyzePdfMutation.mutate({
      file: analysisFile,
      supplierName: analysisSupplier || undefined,
    });
  };

  const handlePredictConfidence = () => {
    if (!predictionTemplate || !predictionText.trim()) {
      enqueueSnackbar('Template and text content are required', { variant: 'error' });
      return;
    }

    predictConfidenceMutation.mutate({
      template_id: predictionTemplate,
      text_content: predictionText,
    });
  };

  const addTextSample = () => {
    setTextSamples(prev => [...prev, '']);
  };

  const updateTextSample = (index: number, value: string) => {
    setTextSamples(prev => prev.map((t, i) => i === index ? value : t));
  };

  const removeTextSample = (index: number) => {
    setTextSamples(prev => prev.filter((_, i) => i !== index));
  };

  const addPattern = () => {
    setExistingPatterns(prev => [...prev, '']);
  };

  const updatePattern = (index: number, value: string) => {
    setExistingPatterns(prev => prev.map((p, i) => i === index ? value : p));
  };

  const removePattern = (index: number) => {
    setExistingPatterns(prev => prev.filter((_, i) => i !== index));
  };

  const removeSampleFile = (index: number) => {
    setSampleFiles(prev => prev.filter((_, i) => i !== index));
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'success';
    if (confidence > 0.6) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        <SmartToy sx={{ mr: 1, verticalAlign: 'middle' }} />
        ML Features
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Use machine learning to automatically generate templates, analyze patterns, and improve extraction accuracy.
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} aria-label="ML features tabs">
          <Tab label="Auto-Generate Template" icon={<AutoFixHigh />} />
          <Tab label="Analyze PDF" icon={<Psychology />} />
          <Tab label="Pattern Analysis" icon={<Analytics />} />
          <Tab label="Confidence Prediction" icon={<TrendingUp />} />
          <Tab label="Model Status" icon={<ModelTraining />} />
        </Tabs>

        {/* Auto-Generate Template */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <AutoFixHigh sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Template Generation
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      label="Supplier Name"
                      value={supplierName}
                      onChange={(e) => setSupplierName(e.target.value)}
                      placeholder="e.g., KPN, Dustin Nederland, VDX"
                      required
                      fullWidth
                    />
                    
                    <TextField
                      label="Template ID (Optional)"
                      value={templateId}
                      onChange={(e) => setTemplateId(e.target.value)}
                      placeholder="e.g., kpn_auto, dustin_ml"
                      helperText="Leave empty to auto-generate"
                      fullWidth
                    />
                    
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        Confidence Threshold: {Math.round(confidenceThreshold * 100)}%
                      </Typography>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.1"
                        value={confidenceThreshold}
                        onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                        style={{ width: '100%' }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        Hogere waarden = meer zekerheid vereist voor patroondetectie
                      </Typography>
                    </Box>
                    
                    <Box
                      {...getSampleProps()}
                      sx={{
                        border: '2px dashed #ccc',
                        borderRadius: 2,
                        p: 3,
                        textAlign: 'center',
                        cursor: 'pointer',
                        '&:hover': { borderColor: 'primary.main' },
                      }}
                    >
                      <input {...getSampleInputs()} />
                      <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography variant="body1">
                        Drop sample PDF files here or click to select
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Upload 2-5 sample invoices from the same supplier
                      </Typography>
                    </Box>
                    
                    {sampleFiles.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Sample Files ({sampleFiles.length}):
                        </Typography>
                        <List dense>
                          {sampleFiles.map((file, index) => (
                            <ListItem
                              key={index}
                              secondaryAction={
                                <Button
                                  size="small"
                                  color="error"
                                  onClick={() => removeSampleFile(index)}
                                >
                                  <Delete />
                                </Button>
                              }
                            >
                              <ListItemText primary={file.name} secondary={`${(file.size / 1024).toFixed(1)} KB`} />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                    
                    <Button
                      variant="contained"
                      onClick={handleGenerateTemplate}
                      disabled={generateTemplateMutation.isLoading || !supplierName.trim() || sampleFiles.length === 0}
                      startIcon={generateTemplateMutation.isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
                      fullWidth
                    >
                      {generateTemplateMutation.isLoading ? 'Generating Template...' : 'Generate Template'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {generationResult && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <CheckCircle color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Template Gegenereerd
                    </Typography>
                    
                    <Alert 
                      severity={
                        generationResult.confidence_score > 0.8 ? 'success' : 
                        generationResult.confidence_score > 0.6 ? 'warning' : 'error'
                      } 
                      sx={{ mb: 2 }}
                    >
                      Template "{generationResult.template_name}" aangemaakt met {Math.round(generationResult.confidence_score * 100)}% zekerheid
                    </Alert>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Template ID: <strong>{generationResult.template_id}</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Gebaseerd op {sampleFiles.length} sample bestand(en)
                      </Typography>
                    </Box>
                    
                    <Accordion defaultExpanded>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Gedetecteerde Velden ({Object.keys(generationResult.field_mappings || {}).length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        {/* Smart field validation alerts */}
                        {(() => {
                          const suspiciousFields = Object.entries(generationResult.field_mappings || {}).filter(([key, value]) => {
                            const val = String(value);
                            return (
                              (key === 'invoice_number' && val.toLowerCase().includes('looking for')) ||
                              (key === 'supplier_name' && val.toLowerCase().includes('looking for')) ||
                              (key.includes('amount') && val.toLowerCase().includes('looking for')) ||
                              val === key // Field name same as key means no value found
                            );
                          });
                          
                          if (suspiciousFields.length > 0) {
                            return (
                              <Alert severity="warning" sx={{ mb: 2 }}>
                                <strong>⚠️ Ontbrekende of onvolledige velden gedetecteerd!</strong><br/>
                                De volgende velden hebben geen goede waarden gevonden:
                                <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                                  {suspiciousFields.map(([field, value]) => (
                                    <li key={field}>
                                      <strong>{field}</strong>: {String(value)}
                                    </li>
                                  ))}
                                </ul>
                                <Typography variant="body2" sx={{ mt: 1 }}>
                                  💡 <strong>Tip:</strong> Probeer een hogere confidence threshold of upload een duidelijkere PDF.
                                </Typography>
                              </Alert>
                            );
                          }
                          return null;
                        })()}
                        
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          {Object.entries(generationResult.field_mappings || {}).map(([key, value]) => {
                            const valueStr = String(value);
                            const isIncomplete = valueStr.toLowerCase().includes('looking for') || valueStr === key;
                            const isGoodValue = valueStr && !isIncomplete && valueStr.length > 2;
                            
                            return (
                              <Box 
                                key={key} 
                                sx={{ 
                                  display: 'flex', 
                                  justifyContent: 'space-between', 
                                  p: 1, 
                                  bgcolor: isGoodValue ? 'success.light' : isIncomplete ? 'warning.light' : 'background.default', 
                                  borderRadius: 1,
                                  border: isGoodValue ? '1px solid' : isIncomplete ? '1px solid' : 'none',
                                  borderColor: isGoodValue ? 'success.main' : isIncomplete ? 'warning.main' : 'transparent'
                                }}
                              >
                                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                                  {key.replace('_', ' ')}:
                                  {isGoodValue && <span style={{ color: 'green' }}> ✓</span>}
                                  {isIncomplete && <span style={{ color: 'orange' }}> ⚠️</span>}
                                </Typography>
                                <Typography variant="body2" sx={{ 
                                  color: isGoodValue ? 'success.dark' : isIncomplete ? 'warning.dark' : 'inherit',
                                  fontWeight: isGoodValue ? 'bold' : 'normal'
                                }}>
                                  {valueStr || 'Niet gevonden'}
                                </Typography>
                              </Box>
                            );
                          })}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Extractie Patronen ({generationResult.suggested_patterns?.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {generationResult.suggested_patterns?.map((pattern: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={pattern.name || pattern.pattern}
                                secondary={`Veld: ${pattern.field_name || 'Onbekend'} | Regex: ${pattern.pattern || 'Niet gedefinieerd'}`}
                              />
                              <Chip
                                label={`${Math.round((pattern.confidence || 0) * 100)}%`}
                                color={getConfidenceColor(pattern.confidence || 0) as any}
                                size="small"
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Leverancier Detectie ({generationResult.supplier_patterns?.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {generationResult.supplier_patterns?.map((pattern: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={pattern.pattern || 'Geen patroon'}
                                secondary={`Type: ${pattern.type || 'Tekst'} | Voor leverancier herkenning`}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>

                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button
                        variant="contained"
                        color="warning"
                        onClick={() => {
                          // Test het template met de sample PDF
                          if (sampleFiles.length > 0 && generationResult?.template_id) {
                            testTemplateMutation.mutate({
                              templateId: generationResult.template_id,
                              file: sampleFiles[0],
                            });
                          }
                        }}
                        size="small"
                        disabled={sampleFiles.length === 0 || !generationResult?.template_id || testTemplateMutation.isLoading}
                        startIcon={testTemplateMutation.isLoading ? <CircularProgress size={16} /> : undefined}
                      >
                        {testTemplateMutation.isLoading ? 'Testen...' : 'Template Testen'}
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={() => {
                          // Navigeer naar templates pagina
                          window.location.href = '/templates';
                        }}
                        size="small"
                      >
                        Template Bekijken
                      </Button>
                      <Button
                        variant="outlined"
                        color="secondary"
                        onClick={() => {
                          setGenerationResult(null);
                          setSampleFiles([]);
                          setSupplierName('');
                          setTemplateId('');
                        }}
                        size="small"
                      >
                        Nieuw Template
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Grid>

            {/* Template Test Results */}
            {templateTestResult && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <CheckCircle color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Template Test Resultaten
                    </Typography>
                    
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Template "{templateTestResult.template_name}" getest met sample PDF
                    </Alert>

                    <Accordion defaultExpanded>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Extractie Details ({Object.keys(templateTestResult.extraction_details || {}).length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {Object.entries(templateTestResult.extraction_details || {}).map(([field, details]: [string, any]) => (
                            <Box key={field} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                                  {field}
                                </Typography>
                                <Chip
                                  label={`${Math.round((details.confidence || 0) * 100)}%`}
                                  color={getConfidenceColor(details.confidence || 0) as any}
                                  size="small"
                                />
                              </Box>
                              
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                <strong>Waarde:</strong> {String(details.value) || 'Niet gevonden'}
                              </Typography>
                              
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                <strong>Methode:</strong> {details.found_by}
                              </Typography>
                              
                              {details.matched_patterns && details.matched_patterns.length > 0 && (
                                <Box>
                                  <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                    Gevonden patronen:
                                  </Typography>
                                  {details.matched_patterns.map((pattern: any, idx: number) => (
                                    <Box key={idx} sx={{ ml: 2, mb: 1 }}>
                                      <Typography variant="caption" sx={{ fontFamily: 'monospace', bgcolor: 'background.default', p: 0.5, borderRadius: 0.5 }}>
                                        {pattern.pattern}
                                      </Typography>
                                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                                        Matches: {pattern.matches.join(', ')} ({pattern.match_count} totaal)
                                      </Typography>
                                    </Box>
                                  ))}
                                </Box>
                              )}
                            </Box>
                          ))}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </TabPanel>

        {/* Analyze PDF */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <Psychology sx={{ mr: 1, verticalAlign: 'middle' }} />
                    PDF Analyse
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      label="Leverancier Naam (Optioneel)"
                      value={analysisSupplier}
                      onChange={(e) => setAnalysisSupplier(e.target.value)}
                      placeholder="bijv. KPN, Dustin Nederland"
                      helperText="Laat leeg voor automatische detectie"
                      fullWidth
                    />
                    
                    <Box
                      {...getAnalysisProps()}
                      sx={{
                        border: '2px dashed #ccc',
                        borderRadius: 2,
                        p: 3,
                        textAlign: 'center',
                        cursor: 'pointer',
                        '&:hover': { borderColor: 'primary.main' },
                      }}
                    >
                      <input {...getAnalysisInputs()} />
                      <FileUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography variant="body1">
                        Sleep een PDF bestand hierheen of klik om te selecteren
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Analyseer structuur en stel extractie patronen voor
                      </Typography>
                    </Box>
                    
                    {analysisFile && (
                      <Alert severity="info">
                        Geselecteerd: {analysisFile.name} ({(analysisFile.size / 1024).toFixed(1)} KB)
                      </Alert>
                    )}
                    
                    <Button
                      variant="contained"
                      onClick={handleAnalyzePdf}
                      disabled={analyzePdfMutation.isLoading || !analysisFile}
                      startIcon={analyzePdfMutation.isLoading ? <CircularProgress size={20} /> : <Biotech />}
                      fullWidth
                    >
                      {analyzePdfMutation.isLoading ? 'PDF Analyseren...' : 'PDF Analyseren'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {pdfAnalysisResult && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <Insights color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Analysis Results
                    </Typography>
                    
                    <Alert severity="success" sx={{ mb: 2 }}>
                      Analysis completed with {Math.round(pdfAnalysisResult.confidence_score * 100)}% confidence
                    </Alert>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Detected Supplier:</Typography>
                      <Typography variant="body1">{pdfAnalysisResult.template_name}</Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Button
                        variant="contained"
                        color="secondary"
                        onClick={() => {
                          // Create template from analyzed PDF
                          if (analysisFile) {
                            generateTemplateMutation.mutate({
                              supplierName: pdfAnalysisResult.template_name || analysisSupplier || 'Unknown',
                              templateId: pdfAnalysisResult.template_id,
                              sampleFiles: [analysisFile],
                              confidenceThreshold: 0.5,
                            });
                          }
                        }}
                        disabled={!analysisFile || generateTemplateMutation.isLoading}
                        startIcon={<Save />}
                        fullWidth
                      >
                        Template Aanmaken van Deze PDF
                      </Button>
                    </Box>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Geëxtraheerde Velden ({Object.keys(pdfAnalysisResult.field_mappings || {}).length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        {/* Validation warnings */}
                        {(pdfAnalysisResult.field_mappings?.invoice_number === "Brouwer" || 
                          pdfAnalysisResult.field_mappings?.supplier_name === "Totaal inc" ||
                          !pdfAnalysisResult.field_mappings?.total_amount) && (
                          <Alert severity="warning" sx={{ mb: 2 }}>
                            ⚠️ <strong>Verdachte extractie resultaten gedetecteerd!</strong><br/>
                            Controleer de velden hieronder - sommige lijken incorrect:
                            <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                              {pdfAnalysisResult.field_mappings?.invoice_number === "Brouwer" && 
                                <li>"Brouwer" lijkt geen geldig factuurnummer</li>}
                              {pdfAnalysisResult.field_mappings?.supplier_name === "Totaal inc" && 
                                <li>"Totaal inc" lijkt geen geldige leveranciersnaam</li>}
                              {!pdfAnalysisResult.field_mappings?.total_amount && 
                                <li>Geen totaalbedrag gevonden</li>}
                            </ul>
                          </Alert>
                        )}
                        
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          {Object.entries(pdfAnalysisResult.field_mappings || {}).map(([field, value]) => {
                            // Determine if this field looks suspicious
                            const isSuspicious = 
                              (field === 'invoice_number' && (value === 'Brouwer' || value === 'Totaal inc')) ||
                              (field === 'supplier_name' && (value === 'Totaal inc' || value === 'Brouwer')) ||
                              (field.includes('amount') && !value);
                            
                            return (
                              <Box 
                                key={field} 
                                sx={{ 
                                  display: 'flex', 
                                  justifyContent: 'space-between', 
                                  p: 1, 
                                  bgcolor: isSuspicious ? 'error.light' : 'background.default', 
                                  borderRadius: 1,
                                  border: isSuspicious ? '1px solid' : 'none',
                                  borderColor: isSuspicious ? 'error.main' : 'transparent'
                                }}
                              >
                                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                                  {field}:
                                  {isSuspicious && <span style={{ color: 'red' }}> ⚠️</span>}
                                </Typography>
                                <Typography variant="body2" sx={{ color: isSuspicious ? 'error.main' : 'inherit' }}>
                                  {String(value) || 'Niet gevonden'}
                                </Typography>
                              </Box>
                            );
                          })}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Suggested Patterns ({pdfAnalysisResult.suggested_patterns?.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {pdfAnalysisResult.suggested_patterns?.map((pattern: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={pattern.name || 'Pattern'}
                                secondary={pattern.pattern}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">PDF Text Preview</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ 
                          maxHeight: 300, 
                          overflow: 'auto', 
                          p: 2, 
                          bgcolor: 'background.default', 
                          borderRadius: 1, 
                          fontFamily: 'monospace',
                          fontSize: '0.85rem',
                          lineHeight: 1.4
                        }}>
                          {pdfAnalysisResult.raw_text_preview || 'No text preview available'}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Pattern Analysis */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <Analytics sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Pattern Analysis
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Field Type</InputLabel>
                      <Select
                        value={fieldType}
                        label="Field Type"
                        onChange={(e) => setFieldType(e.target.value)}
                      >
                        <MenuItem value="text">Text</MenuItem>
                        <MenuItem value="amount">Amount</MenuItem>
                        <MenuItem value="date">Date</MenuItem>
                        <MenuItem value="number">Number</MenuItem>
                        <MenuItem value="vat_number">VAT Number</MenuItem>
                        <MenuItem value="email">Email</MenuItem>
                        <MenuItem value="phone">Phone</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <Typography variant="subtitle2">Text Samples:</Typography>
                    {textSamples.map((sample, index) => (
                      <Box key={index} sx={{ display: 'flex', gap: 1 }}>
                        <TextField
                          label={`Sample ${index + 1}`}
                          value={sample}
                          onChange={(e) => updateTextSample(index, e.target.value)}
                          multiline
                          rows={2}
                          fullWidth
                        />
                        {textSamples.length > 1 && (
                          <Button
                            color="error"
                            onClick={() => removeTextSample(index)}
                            sx={{ minWidth: 'auto' }}
                          >
                            <Delete />
                          </Button>
                        )}
                      </Box>
                    ))}
                    
                    <Button
                      variant="outlined"
                      startIcon={<Add />}
                      onClick={addTextSample}
                      size="small"
                    >
                      Add Text Sample
                    </Button>
                    
                    <Typography variant="subtitle2">Existing Patterns (Optional):</Typography>
                    {existingPatterns.map((pattern, index) => (
                      <Box key={index} sx={{ display: 'flex', gap: 1 }}>
                        <TextField
                          label={`Pattern ${index + 1}`}
                          value={pattern}
                          onChange={(e) => updatePattern(index, e.target.value)}
                          placeholder="e.g., \\d{2}-\\d{2}-\\d{4}"
                          fullWidth
                        />
                        {existingPatterns.length > 1 && (
                          <Button
                            color="error"
                            onClick={() => removePattern(index)}
                            sx={{ minWidth: 'auto' }}
                          >
                            <Delete />
                          </Button>
                        )}
                      </Box>
                    ))}
                    
                    <Button
                      variant="outlined"
                      startIcon={<Add />}
                      onClick={addPattern}
                      size="small"
                    >
                      Add Pattern
                    </Button>
                    
                    <Button
                      variant="contained"
                      onClick={handleAnalyzePatterns}
                      disabled={analyzePatternsMutation.isLoading}
                      startIcon={analyzePatternsMutation.isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
                      fullWidth
                    >
                      {analyzePatternsMutation.isLoading ? 'Analyzing...' : 'Analyze Patterns'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {analysisResult && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <CheckCircle color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Pattern Analysis Results
                    </Typography>
                    
                    <Alert 
                      severity={analysisResult.pattern_coverage > 0.8 ? 'success' : analysisResult.pattern_coverage > 0.5 ? 'warning' : 'error'}
                      sx={{ mb: 2 }}
                    >
                      Pattern Coverage: {Math.round(analysisResult.pattern_coverage * 100)}%
                    </Alert>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Suggested Patterns ({analysisResult.suggested_patterns?.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {analysisResult.suggested_patterns?.map((pattern: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={pattern.pattern}
                                secondary={`Confidence: ${Math.round((analysisResult.confidence_scores?.[index] || 0) * 100)}%`}
                              />
                              <Chip
                                label={`${Math.round((analysisResult.confidence_scores?.[index] || 0) * 100)}%`}
                                color={getConfidenceColor(analysisResult.confidence_scores?.[index] || 0) as any}
                                size="small"
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Recommendations ({analysisResult.recommendations?.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {analysisResult.recommendations?.map((rec: string, index: number) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Warning color="warning" />
                              </ListItemIcon>
                              <ListItemText primary={rec} />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Confidence Prediction */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Confidence Prediction
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Template</InputLabel>
                      <Select
                        value={predictionTemplate}
                        label="Template"
                        onChange={(e) => setPredictionTemplate(e.target.value)}
                      >
                        {templates.map((template) => (
                          <MenuItem key={template.template_id} value={template.template_id}>
                            {template.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    
                    <TextField
                      label="Text Content"
                      value={predictionText}
                      onChange={(e) => setPredictionText(e.target.value)}
                      multiline
                      rows={6}
                      placeholder="Paste invoice text here to predict extraction quality..."
                      fullWidth
                    />
                    
                    <Button
                      variant="contained"
                      onClick={handlePredictConfidence}
                      disabled={predictConfidenceMutation.isLoading || !predictionTemplate || !predictionText.trim()}
                      startIcon={predictConfidenceMutation.isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
                      fullWidth
                    >
                      {predictConfidenceMutation.isLoading ? 'Predicting...' : 'Predict Confidence'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {predictionResult && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <TrendingUp color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Confidence Prediction
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Overall Confidence: {Math.round(predictionResult.overall_confidence * 100)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={predictionResult.overall_confidence * 100}
                        color={getConfidenceColor(predictionResult.overall_confidence) as any}
                        sx={{ height: 10, borderRadius: 5 }}
                      />
                    </Box>
                    
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Quality Score: {Math.round(predictionResult.quality_score * 100)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={predictionResult.quality_score * 100}
                        color={getConfidenceColor(predictionResult.quality_score) as any}
                        sx={{ height: 10, borderRadius: 5 }}
                      />
                    </Box>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">Field Confidences</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {Object.entries(predictionResult.field_confidences || {}).map(([field, confidence]) => (
                            <ListItem key={field}>
                              <ListItemText primary={field} />
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 100 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={(confidence as number) * 100}
                                  color={getConfidenceColor(confidence as number) as any}
                                  sx={{ flexGrow: 1, height: 6 }}
                                />
                                <Typography variant="body2">
                                  {Math.round((confidence as number) * 100)}%
                                </Typography>
                              </Box>
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="subtitle1">
                          Recommendations ({predictionResult.recommendations?.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {predictionResult.recommendations?.map((rec: string, index: number) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Warning color="info" />
                              </ListItemIcon>
                              <ListItemText primary={rec} />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Model Status */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <ModelTraining sx={{ mr: 1, verticalAlign: 'middle' }} />
                    ML Model Status
                  </Typography>
                  
                  {mlModels ? (
                    <List>
                      {mlModels.models.map((model, index) => (
                        <React.Fragment key={model.name}>
                          <ListItem>
                            <ListItemIcon>
                              {model.status === 'available' ? (
                                <CheckCircle color="success" />
                              ) : model.status === 'training' ? (
                                <CircularProgress size={24} />
                              ) : (
                                <Error color="error" />
                              )}
                            </ListItemIcon>
                            <ListItemText
                              primary={model.name}
                              secondary={
                                <Box>
                                  <Typography variant="body2">
                                    {model.description}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    Version: {model.version} | Status: {model.status}
                                  </Typography>
                                </Box>
                              }
                            />
                            <Chip
                              label={model.status}
                              color={
                                model.status === 'available' ? 'success' :
                                model.status === 'training' ? 'warning' : 'error'
                              }
                              size="small"
                            />
                          </ListItem>
                          {index < mlModels.models.length - 1 && <Divider />}
                        </React.Fragment>
                      ))}
                    </List>
                  ) : (
                    <Alert severity="info">Loading model information...</Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default MLPage;