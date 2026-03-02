// Admin Interface JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminInterface();
});

function initializeAdminInterface() {
    // Initialize tab switching functionality
    initializeTabSwitching();

    // Load existing configuration
    loadConfiguration();

    // Initialize event listeners
    initializeEventListeners();
}

function initializeTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const configForms = document.querySelectorAll('.config-form');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all tabs and forms
            tabButtons.forEach(btn => btn.classList.remove('active'));
            configForms.forEach(form => {
                form.classList.remove('active');
                form.style.display = 'none';
            });

            // Add active class to clicked tab
            this.classList.add('active');

            // Show corresponding form
            const targetForm = document.getElementById(targetTab + '-config');
            if (targetForm) {
                targetForm.classList.add('active');
                targetForm.style.display = 'block';
            }

            // Update current tab reference
            window.currentTab = targetTab;
        });
    });
}

function initializeEventListeners() {
    // Save configuration button
    const saveConfigBtn = document.getElementById('saveConfig');
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveConfiguration);
    }



    // Add question button
    const addQuestionBtn = document.getElementById('addQuestionBtn');
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', function() {
            if (window.currentTab && window.currentTab !== 'forms') {
                addQuestion(window.currentTab);
            }
        });
    }

    // Refresh forms button
    const refreshFormsBtn = document.getElementById('refreshForms');
    if (refreshFormsBtn) {
        refreshFormsBtn.addEventListener('click', loadForms);
    }

    // Manual item creation button
    const createManualItemBtn = document.getElementById('createManualItem');
    if (createManualItemBtn) {
        createManualItemBtn.addEventListener('click', createManualItem);
    }
}

// Set initial tab
window.currentTab = 'clientes';

// Configuration management functions
function loadConfiguration() {
    console.log('Loading configuration from /api/config...');
    fetch('/api/config')
        .then(response => {
            console.log('Config response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(config => {
            console.log('Loaded config:', config);
            populateConfigurationForm(config);
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            // Try to load config.json directly as fallback
            console.log('Trying fallback config loading...');
            loadFallbackConfig();
        });
}

function loadFallbackConfig() {
    fetch('/static/config.json')
        .then(response => response.json())
        .then(config => {
            console.log('Loaded fallback config:', config);
            populateConfigurationForm(config);
        })
        .catch(error => {
            console.error('Error loading fallback configuration:', error);
        });
}

function populateConfigurationForm(config) {
    console.log('Populating configuration form with:', config);

    // Populate form fields for each tab
    ['guias', 'clientes', 'fornecedores'].forEach(formType => {
        console.log(`Processing form type: ${formType}`);
        const formConfig = config[formType] || {};
        console.log(`Config for ${formType}:`, formConfig);

        // Populate basic fields
        const boardAField = document.getElementById(`${formType}-board-a`);
        const boardBField = document.getElementById(`${formType}-board-b`);
        const linkColumnField = document.getElementById(`${formType}-link-column`);

        if (boardAField) {
            boardAField.value = formConfig.board_a || '';
            console.log(`Set ${formType} board_a to:`, formConfig.board_a);
        }
        if (boardBField) {
            boardBField.value = formConfig.board_b || '';
            console.log(`Set ${formType} board_b to:`, formConfig.board_b);
        }
        if (linkColumnField) {
            linkColumnField.value = formConfig.link_column || '';
            console.log(`Set ${formType} link_column to:`, formConfig.link_column);
        }

        // Populate header fields
        if (formConfig.header_fields) {
            console.log(`Processing ${formConfig.header_fields.length} header fields for ${formType}`);
            formConfig.header_fields.forEach((field, index) => {
                const titleField = document.getElementById(`${formType}-header-${index + 1}-title`);
                const columnField = document.getElementById(`${formType}-header-${index + 1}-column`);

                if (titleField) {
                    titleField.value = field.title || '';
                    console.log(`Set header ${index + 1} title to:`, field.title);
                }
                if (columnField) {
                    columnField.value = field.monday_column || '';
                    console.log(`Set header ${index + 1} column to:`, field.monday_column);
                }
            });
        }

        // Populate questions
        if (formConfig.questions && formConfig.questions.length > 0) {
            console.log(`Rendering ${formConfig.questions.length} questions for ${formType}`);
            renderQuestions(formType, formConfig.questions);
        } else {
            console.log(`No questions found for ${formType}`);
        }
    });
}

function renderQuestions(formType, questions) {
    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Clear existing questions
    questionsContainer.innerHTML = '';

    if (!questions || questions.length === 0) {
        console.log('No questions to render for:', formType);
        return;
    }

    console.log(`Rendering ${questions.length} questions for ${formType}:`, questions);

    questions.forEach((question, index) => {
        const questionElement = createQuestionElement(formType, question, index);
        questionsContainer.appendChild(questionElement);
    });

    // Re-initialize any icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function createQuestionElement(formType, question, index) {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-item mb-4 p-3 border rounded';
    questionDiv.setAttribute('data-question-id', question.id);

    let questionHtml = '';

    if (question.type === 'divider') {
        questionHtml = `
            <div class="divider-question">
                <h5 class="text-primary">
                    <i data-feather="minus"></i>
                    ${question.title || 'Divisor'}
                </h5>
                <div class="row">
                    <div class="col-md-8">
                        <label class="form-label">Título do Divisor:</label>
                        <input type="text" class="form-control" value="${question.title || ''}" 
                               onchange="updateQuestionField('${formType}', ${index}, 'title', this.value)">
                    </div>
                    <div class="col-md-4 d-flex align-items-end">
                        <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion('${formType}', ${index})">
                            <i data-feather="trash-2"></i> Remover
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        const typeOptions = {
            'text': 'Texto',
            'longtext': 'Texto Longo',
            'yesno': 'Sim/Não',
            'rating': 'Avaliação (1-10)',
            'dropdown': 'Lista Suspensa',
            'monday_column': 'Coluna Monday'
        };

        questionHtml = `
            <div class="regular-question">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">Pergunta ${index + 1}</h6>
                    <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion('${formType}', ${index})">
                        <i data-feather="trash-2"></i> Remover
                    </button>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Tipo:</label>
                        <select class="form-control" onchange="updateQuestionField('${formType}', ${index}, 'type', this.value)">
                            ${Object.entries(typeOptions).map(([value, text]) => 
                                `<option value="${value}" ${question.type === value ? 'selected' : ''}>${text}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Obrigatória:</label>
                        <select class="form-control" onchange="updateQuestionField('${formType}', ${index}, 'required', this.value === 'true')">
                            <option value="false" ${!question.required ? 'selected' : ''}>Não</option>
                            <option value="true" ${question.required ? 'selected' : ''}>Sim</option>
                        </select>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Texto da Pergunta:</label>
                        <textarea class="form-control" rows="2" 
                                  onchange="updateQuestionField('${formType}', ${index}, 'text', this.value)">${question.text || ''}</textarea>
                    </div>
                </div>

                ${question.type === 'dropdown' ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Opções (separadas por ponto e vírgula):</label>
                        <input type="text" class="form-control" value="${question.dropdown_options || ''}"
                               placeholder="Opção 1;Opção 2;Opção 3"
                               onchange="updateQuestionField('${formType}', ${index}, 'dropdown_options', this.value)">
                    </div>
                </div>
                ` : ''}

                ${question.type === 'monday_column' ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Coluna de Origem (Monday):</label>
                        <input type="text" class="form-control" value="${question.source_column || ''}"
                               placeholder="Ex: text_mkrj9z52, dropdown_mksd123"
                               onchange="updateQuestionField('${formType}', ${index}, 'source_column', this.value)">
                        <small class="form-text text-muted">ID da coluna do Monday.com que será usada como nome/valor da pergunta</small>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino - Texto:</label>
                        <input type="text" class="form-control" value="${question.text_destination_column || question.destination_column || ''}"
                               placeholder="Ex: text_mkhotel_name"
                               onchange="updateQuestionField('${formType}', ${index}, 'text_destination_column', this.value)">
                        <small class="form-text text-muted">Onde salvar o nome/texto do item</small>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino - Avaliação:</label>
                        <input type="text" class="form-control" value="${question.rating_destination_column || ''}"
                               placeholder="Ex: numeric_mkrjpfxv"
                               onchange="updateQuestionField('${formType}', ${index}, 'rating_destination_column', this.value)">
                        <small class="form-text text-muted">Onde salvar a nota (1-10)</small>
                    </div>
                </div>
                ` : `
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino (Monday):</label>
                        <input type="text" class="form-control" value="${question.destination_column || ''}"
                               placeholder="Ex: text_mksd123"
                               onchange="updateQuestionField('${formType}', ${index}, 'destination_column', this.value)">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">ID da Pergunta:</label>
                        <input type="text" class="form-control" value="${question.id || ''}" readonly>
                    </div>
                </div>
                `}

                ${question.type !== 'monday_column' ? `
                <div class="row mt-3">
                    <div class="col-md-6"></div>
                    <div class="col-md-6">
                        <label class="form-label">ID da Pergunta:</label>
                        <input type="text" class="form-control" value="${question.id || ''}" readonly>
                    </div>
                </div>
                ` : ''}

                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Depende da pergunta (Sim/Não):</label>
                        <select class="form-control conditional-depends-on" onchange="updateQuestionConditional('${formType}', ${index}, 'depends_on', this.value)">
                            <option value="">Nenhuma</option>
                            ${getAllYesNoQuestions(formType).map(q => 
                                `<option value="${q.id}" ${question.conditional && question.conditional.depends_on === q.id ? 'selected' : ''}>${q.text || q.id}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Mostrar se a resposta for:</label>
                        <select class="form-control conditional-show-if" onchange="updateQuestionConditional('${formType}', ${index}, 'show_if', this.value)">
                            <option value="">Qualquer resposta</option>
                            <option value="Sim" ${question.conditional && question.conditional.show_if === 'Sim' ? 'selected' : ''}>Sim</option>
                            <option value="Não" ${question.conditional && question.conditional.show_if === 'Não' ? 'selected' : ''}>Não</option>
                        </select>
                    </div>
                </div>

                ${question.conditional ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <strong>Pergunta Condicional:</strong> Depende de "${question.conditional.depends_on}"
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    questionDiv.innerHTML = questionHtml;
    return questionDiv;
}

function updateQuestionConditional(formType, index, field, value) {
    const currentQuestions = getCurrentQuestions(formType);
    if (currentQuestions[index]) {
        if (!currentQuestions[index].conditional) {
            currentQuestions[index].conditional = {};
        }
        currentQuestions[index].conditional[field] = value;
    }
}

// Question management functions
function addQuestion(formType) {
    if (!formType) {
        console.error('Form type is required');
        return;
    }

    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Get current questions from the rendered form
    const currentQuestions = getCurrentQuestions(formType);

    // Create new question with unique ID
    const newQuestion = {
        id: `question_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'text',
        text: '',
        required: false,
        destination_column: '',
        source: 'manual',
        is_conditional: false
    };

    // Add to current questions array
    currentQuestions.push(newQuestion);

    // Re-render questions with updated array
    renderQuestions(formType, currentQuestions);

    console.log('Added new question to', formType);
}

function removeQuestion(formType, index) {
    if (!formType) {
        console.error('Form type is required');
        return;
    }

    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Get current questions from the rendered form
    const currentQuestions = getCurrentQuestions(formType);

    if (index >= 0 && index < currentQuestions.length) {
        // Remove the question at the specified index
        currentQuestions.splice(index, 1);

        // Re-render questions with updated array
        renderQuestions(formType, currentQuestions);
    } else {
        console.error('Invalid index for removing question:', index);
    }
}

function updateQuestionField(formType, index, field, value) {
    if (!formType) {
        console.error('Form type is required');
        return;
    }

    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Get current questions from the rendered form
    const currentQuestions = getCurrentQuestions(formType);

    if (currentQuestions && currentQuestions[index]) {
        // Update the field for the question at the specified index
        currentQuestions[index][field] = value;

        // Re-render questions with updated array
        renderQuestions(formType, currentQuestions);
    } else {
        console.error('Invalid index or questions array for updating question field:', index);
    }
}

function getCurrentQuestions(formType) {
    // Attempt to get questions from the DOM
    try {
        const questionsContainer = document.getElementById(`${formType}-questions`);
        if (!questionsContainer) {
            console.warn('Questions container not found:', `${formType}-questions`);
            return []; // Return an empty array
        }

        // Collect question items from the DOM
        const questionItems = questionsContainer.querySelectorAll('.question-item');
        const questions = [];

        questionItems.forEach(item => {
            const questionId = item.getAttribute('data-question-id');
            let question = null;

            // Find existing question (if available)
            if (questionId) {
                question = questions.find(q => q.id === questionId);
            }

            if (!question) {
                question = { id: questionId };
                questions.push(question);
            }
        });

        // Map values from the DOM back to the question objects
        return questions;

    } catch (error) {
        console.error('Error getting current questions:', error);
        return [];
    }
}

function saveConfiguration() {
    const config = {
        guias: extractFormConfig('guias'),
        clientes: extractFormConfig('clientes'),
        fornecedores: extractFormConfig('fornecedores')
    };

    console.log('Saving configuration:', config);

    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Save response:', data);
        if (data.error) {
            alert('Erro ao salvar configuração: ' + data.error);
        } else {
            // Copy configuration to clipboard
            const jsonString = JSON.stringify(config, null, 2);
            copyConfigToClipboard(jsonString);

            // Show only the clipboard success message
            alert('The body of config.json was successfully copied to the clipboard!');

            // Reload configuration to confirm changes were saved
            loadConfiguration();
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
        alert('Erro ao salvar configuração: ' + error.message);
    });
}

function extractFormConfig(formType) {
    const config = {
        board_a: document.getElementById(`${formType}-board-a`)?.value || '',
        board_b: document.getElementById(`${formType}-board-b`)?.value || '',
        link_column: document.getElementById(`${formType}-link-column`)?.value || '',
        header_fields: [],
        questions: []
    };

    // Extract header fields
    for (let i = 1; i <= 4; i++) {
        const titleField = document.getElementById(`${formType}-header-${i}-title`);
        const columnField = document.getElementById(`${formType}-header-${i}-column`);

        if (titleField && columnField) {
            const title = titleField.value.trim();
            const column = columnField.value.trim();

            config.header_fields.push({
                title: title,
                monday_column: column
            });
        }
    }

    // Extract questions
    config.questions = getCurrentQuestions(formType);

    return config;
}

function loadForms() {
    // Load and display created forms
    const formsLoading = document.getElementById('formsLoading');
    const formsEmpty = document.getElementById('formsEmpty');
    const formsList = document.getElementById('formsList');
    const formsCount = document.getElementById('formsCount');

    // Show loading state
    if (formsLoading) formsLoading.style.display = 'block';
    if (formsEmpty) formsEmpty.style.display = 'none';
    if (formsList) formsList.style.display = 'none';

    fetch('/api/forms')
        .then(response => response.json())
        .then(forms => {
            // Hide loading
            if (formsLoading) formsLoading.style.display = 'none';

            if (forms && forms.length > 0) {
                renderFormsList(forms);
                if (formsList) formsList.style.display = 'block';
                if (formsCount) formsCount.textContent = forms.length;
            } else {
                if (formsEmpty) formsEmpty.style.display = 'block';
                if (formsCount) formsCount.textContent = '0';
            }
        })
        .catch(error => {
            console.error('Error loading forms:', error);
            if (formsLoading) formsLoading.style.display = 'none';
            if (formsEmpty) formsEmpty.style.display = 'block';
            if (formsCount) formsCount.textContent = '0';
        });
}

function renderFormsList(forms) {
    const formsList = document.getElementById('formsList');
    if (!formsList) return;

    formsList.innerHTML = '';

    forms.forEach(form => {
        const formCard = createFormCard(form);
        formsList.appendChild(formCard);
    });
}

function createFormCard(form) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-3';

    col.innerHTML = `
        <div class="card h-100">
            <div class="card-body">
                <h6 class="card-title">${form.title || 'Formulário'}</h6>
                <p class="card-text small text-muted">
                    ID: ${form.id}<br>
                    Tipo: ${form.type || 'N/A'}<br>
                    Criado: ${form.created_at || 'N/A'}
                </p>
                <div class="d-flex gap-2">
                    <a href="/form/${form.id}" target="_blank" class="btn btn-primary btn-sm">
                        <i data-feather="external-link"></i> Abrir
                    </a>
                    <button class="btn btn-danger btn-sm" onclick="deleteForm('${form.id}')">
                        <i data-feather="trash-2"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    return col;
}

function deleteForm(formId) {
    if (confirm('Tem certeza que deseja excluir este formulário?')) {
        fetch(`/api/forms/${formId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Erro ao excluir formulário: ' + data.error);
            } else {
                alert('Formulário excluído com sucesso!');
                loadForms(); // Reload the forms list
            }
        })
        .catch(error => {
            console.error('Error deleting form:', error);
            alert('Erro ao excluir formulário');
        });
    }
}

function copyConfigToClipboard(jsonString) {
    // Try to copy to clipboard
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(jsonString).then(() => {
            console.log('config.json copiado para área de transferência!');
        }).catch(err => {
            console.error('Erro ao copiar para área de transferência:', err);
            fallbackCopyToClipboard(jsonString);
        });
    } else {
        fallbackCopyToClipboard(jsonString);
    }
}

function fallbackCopyToClipboard(text) {
    // Fallback method for copying to clipboard
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        console.log('config.json copiado para área de transferência!');
    } catch (err) {
        console.error('Erro ao copiar:', err);
        // Show the JSON in a modal/alert as last resort
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border: 2px solid #ccc;
            border-radius: 10px;
            max-width: 80vw;
            max-height: 80vh;
            overflow: auto;
            z-index: 9999;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;

        modal.innerHTML = `
            <h3>Copie o JSON abaixo:</h3>
            <textarea readonly style="width: 100%; height: 400px; font-family: monospace; font-size: 12px;">${text}</textarea>
            <br><br>
            <button onclick="this.parentElement.remove()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Fechar</button>
        `;

        document.body.appendChild(modal);
    }

    document.body.removeChild(textArea);
}

function switchTab(tabName) {
    console.log('Switching to tab:', tabName);

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Hide all config forms
    document.querySelectorAll('.config-form').forEach(form => {
        form.classList.remove('active');
        form.style.display = 'none';
    });

    // Add active class to clicked tab button
    const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }

    // Show corresponding config form
    const targetForm = document.getElementById(`${tabName}-config`);
    if (targetForm) {
        targetForm.classList.add('active');
        targetForm.style.display = 'block';
        console.log('Showing form:', targetForm.id);
    } else {
        console.error('Target form not found:', `${tabName}-config`);
    }
}

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, initializing admin interface...');
        initializeAdminInterface();
    });
} else {
    console.log('DOM already ready, initializing admin interface...');
    initializeAdminInterface();
}

function getAllYesNoQuestions(formType) {
    // Get current questions for the specific form type
    const currentQuestions = getCurrentQuestions(formType);
    const yesNoQuestions = currentQuestions.filter(q => q.type === 'yesno');
    return yesNoQuestions;
}

//Add conditional questions
function createQuestionElement(formType, question, index) {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-item mb-4 p-3 border rounded';
    questionDiv.setAttribute('data-question-id', question.id);

    let questionHtml = '';

    if (question.type === 'divider') {
        questionHtml = `
            <div class="divider-question">
                <h5 class="text-primary">
                    <i data-feather="minus"></i>
                    ${question.title || 'Divisor'}
                </h5>
                <div class="row">
                    <div class="col-md-8">
                        <label class="form-label">Título do Divisor:</label>
                        <input type="text" class="form-control" value="${question.title || ''}" 
                               onchange="updateQuestionField('${formType}', ${index}, 'title', this.value)">
                    </div>
                    <div class="col-md-4 d-flex align-items-end">
                        <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion('${formType}', ${index})">
                            <i data-feather="trash-2"></i> Remover
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        const typeOptions = {
            'text': 'Texto',
            'longtext': 'Texto Longo',
            'yesno': 'Sim/Não',
            'rating': 'Avaliação (1-10)',
            'dropdown': 'Lista Suspensa',
            'monday_column': 'Coluna Monday'
        };

        questionHtml = `
            <div class="regular-question">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">Pergunta ${index + 1}</h6>
                    <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion('${formType}', ${index})">
                        <i data-feather="trash-2"></i> Remover
                    </button>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Tipo:</label>
                        <select class="form-control" onchange="updateQuestionField('${formType}', ${index}, 'type', this.value)">
                            ${Object.entries(typeOptions).map(([value, text]) => 
                                `<option value="${value}" ${question.type === value ? 'selected' : ''}>${text}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Obrigatória:</label>
                        <select class="form-control" onchange="updateQuestionField('${formType}', ${index}, 'required', this.value === 'true')">
                            <option value="false" ${!question.required ? 'selected' : ''}>Não</option>
                            <option value="true" ${question.required ? 'selected' : ''}>Sim</option>
                        </select>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Texto da Pergunta:</label>
                        <textarea class="form-control" rows="2" 
                                  onchange="updateQuestionField('${formType}', ${index}, 'text', this.value)">${question.text || ''}</textarea>
                    </div>
                </div>

                ${question.type === 'dropdown' ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Opções (separadas por ponto e vírgula):</label>
                        <input type="text" class="form-control" value="${question.dropdown_options || ''}"
                               placeholder="Opção 1;Opção 2;Opção 3"
                               onchange="updateQuestionField('${formType}', ${index}, 'dropdown_options', this.value)">
                    </div>
                </div>
                ` : ''}

                ${question.type === 'monday_column' ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Coluna de Origem (Monday):</label>
                        <input type="text" class="form-control" value="${question.source_column || ''}"
                               placeholder="Ex: text_mkrj9z52, dropdown_mksd123"
                               onchange="updateQuestionField('${formType}', ${index}, 'source_column', this.value)">
                        <small class="form-text text-muted">ID da coluna do Monday.com que será usada como nome/valor da pergunta</small>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino - Texto:</label>
                        <input type="text" class="form-control" value="${question.text_destination_column || question.destination_column || ''}"
                               placeholder="Ex: text_mkhotel_name"
                               onchange="updateQuestionField('${formType}', ${index}, 'text_destination_column', this.value)">
                        <small class="form-text text-muted">Onde salvar o nome/texto do item</small>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino - Avaliação:</label>
                        <input type="text" class="form-control" value="${question.rating_destination_column || ''}"
                               placeholder="Ex: numeric_mkrjpfxv"
                               onchange="updateQuestionField('${formType}', ${index}, 'rating_destination_column', this.value)">
                        <small class="form-text text-muted">Onde salvar a nota (1-10)</small>
                    </div>
                </div>
                ` : `
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino (Monday):</label>
                        <input type="text" class="form-control" value="${question.destination_column || ''}"
                               placeholder="Ex: text_mksd123"
                               onchange="updateQuestionField('${formType}', ${index}, 'destination_column', this.value)">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">ID da Pergunta:</label>
                        <input type="text" class="form-control" value="${question.id || ''}" readonly>
                    </div>
                </div>
                `}

                ${question.type !== 'monday_column' ? `
                <div class="row mt-3">
                    <div class="col-md-6"></div>
                    <div class="col-md-6">
                        <label class="form-label">ID da Pergunta:</label>
                        <input type="text" class="form-control" value="${question.id || ''}" readonly>
                    </div>
                </div>
                ` : ''}

                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Depende da pergunta (Sim/Não):</label>
                        <select class="form-control conditional-depends-on" onchange="updateQuestionConditional('${formType}', ${index}, 'depends_on', this.value)">
                            <option value="">Nenhuma</option>
                            ${getAllYesNoQuestions(formType).map(q => 
                                `<option value="${q.id}" ${question.conditional && question.conditional.depends_on === q.id ? 'selected' : ''}>${q.text || q.id}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Mostrar se a resposta for:</label>
                        <select class="form-control conditional-show-if" onchange="updateQuestionConditional('${formType}', ${index}, 'show_if', this.value)">
                            <option value="">Qualquer resposta</option>
                            <option value="Sim" ${question.conditional && question.conditional.show_if === 'Sim' ? 'selected' : ''}>Sim</option>
                            <option value="Não" ${question.conditional && question.conditional.show_if === 'Não' ? 'selected' : ''}>Não</option>
                        </select>
                    </div>
                </div>

                ${question.conditional ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <strong>Pergunta Condicional:</strong> Depende de "${question.conditional.depends_on}"
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    questionDiv.innerHTML = questionHtml;
    return questionDiv;
}

function updateQuestionConditional(formType, index, field, value) {
    const currentQuestions = getCurrentQuestions(formType);
    if (currentQuestions[index]) {
        if (!currentQuestions[index].conditional) {
            currentQuestions[index].conditional = {};
        }
        currentQuestions[index].conditional[field] = value;
    }
}

// Question management functions
function addQuestion(formType) {
    if (!formType) {
        console.error('Form type is required');
        return;
    }

    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Get current questions from the rendered form
    const currentQuestions = getCurrentQuestions(formType);

    // Create new question with unique ID
    const newQuestion = {
        id: `question_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'text',
        text: '',
        required: false,
        destination_column: '',
        source: 'manual',
        is_conditional: false
    };

    // Add to current questions array
    currentQuestions.push(newQuestion);

    // Re-render questions with updated array
    renderQuestions(formType, currentQuestions);

    console.log('Added new question to', formType);
}

function removeQuestion(formType, index) {
    if (!formType) {
        console.error('Form type is required');
        return;
    }

    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Get current questions from the rendered form
    const currentQuestions = getCurrentQuestions(formType);

    if (index >= 0 && index < currentQuestions.length) {
        // Remove the question at the specified index
        currentQuestions.splice(index, 1);

        // Re-render questions with updated array
        renderQuestions(formType, currentQuestions);
    } else {
        console.error('Invalid index for removing question:', index);
    }
}

function updateQuestionField(formType, index, field, value) {
    if (!formType) {
        console.error('Form type is required');
        return;
    }

    const questionsContainer = document.getElementById(`${formType}-questions`);
    if (!questionsContainer) {
        console.error('Questions container not found for:', formType);
        return;
    }

    // Get current questions from the rendered form
    const currentQuestions = getCurrentQuestions(formType);

    if (currentQuestions && currentQuestions[index]) {
        // Update the field for the question at the specified index
        currentQuestions[index][field] = value;

        // Re-render questions with updated array
        renderQuestions(formType, currentQuestions);
    } else {
        console.error('Invalid index or questions array for updating question field:', index);
    }
}

function getCurrentQuestions(formType) {
    // Attempt to get questions from the DOM
    try {
        const questionsContainer = document.getElementById(`${formType}-questions`);
        if (!questionsContainer) {
            console.warn('Questions container not found:', `${formType}-questions`);
            return []; // Return an empty array
        }

        // Collect question items from the DOM
        const questionItems = questionsContainer.querySelectorAll('.question-item');
        const questions = [];

        questionItems.forEach(item => {
            const questionId = item.getAttribute('data-question-id');
            let question = null;

            // Find existing question (if available)
            if (questionId) {
                question = questions.find(q => q.id === questionId);
            }

            if (!question) {
                question = { id: questionId };
                questions.push(question);
            }
        });

        // Map values from the DOM back to the question objects
        return questions;

    } catch (error) {
        console.error('Error getting current questions:', error);
        return [];
    }
}

function saveConfiguration() {
    const config = {
        guias: extractFormConfig('guias'),
        clientes: extractFormConfig('clientes'),
        fornecedores: extractFormConfig('fornecedores')
    };

    console.log('Saving configuration:', config);

    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Save response:', data);
        if (data.error) {
            alert('Erro ao salvar configuração: ' + data.error);
        } else {
            // Copy configuration to clipboard
            const jsonString = JSON.stringify(config, null, 2);
            copyConfigToClipboard(jsonString);

            // Show only the clipboard success message
            alert('The body of config.json was successfully copied to the clipboard!');

            // Reload configuration to confirm changes were saved
            loadConfiguration();
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
        alert('Erro ao salvar configuração: ' + error.message);
    });
}

function extractFormConfig(formType) {
    const config = {
        board_a: document.getElementById(`${formType}-board-a`)?.value || '',
        board_b: document.getElementById(`${formType}-board-b`)?.value || '',
        link_column: document.getElementById(`${formType}-link-column`)?.value || '',
        header_fields: [],
        questions: []
    };

    // Extract header fields
    for (let i = 1; i <= 4; i++) {
        const titleField = document.getElementById(`${formType}-header-${i}-title`);
        const columnField = document.getElementById(`${formType}-header-${i}-column`);

        if (titleField && columnField) {
            const title = titleField.value.trim();
            const column = columnField.value.trim();

            config.header_fields.push({
                title: title,
                monday_column: column
            });
        }
    }

    // Extract questions
    config.questions = getCurrentQuestions(formType);

    return config;
}

function loadForms() {
    // Load and display created forms
    const formsLoading = document.getElementById('formsLoading');
    const formsEmpty = document.getElementById('formsEmpty');
    const formsList = document.getElementById('formsList');
    const formsCount = document.getElementById('formsCount');

    // Show loading state
    if (formsLoading) formsLoading.style.display = 'block';
    if (formsEmpty) formsEmpty.style.display = 'none';
    if (formsList) formsList.style.display = 'none';

    fetch('/api/forms')
        .then(response => response.json())
        .then(forms => {
            // Hide loading
            if (formsLoading) formsLoading.style.display = 'none';

            if (forms && forms.length > 0) {
                renderFormsList(forms);
                if (formsList) formsList.style.display = 'block';
                if (formsCount) formsCount.textContent = forms.length;
            } else {
                if (formsEmpty) formsEmpty.style.display = 'block';
                if (formsCount) formsCount.textContent = '0';
            }
        })
        .catch(error => {
            console.error('Error loading forms:', error);
            if (formsLoading) formsLoading.style.display = 'none';
            if (formsEmpty) formsEmpty.style.display = 'block';
            if (formsCount) formsCount.textContent = '0';
        });
}

function renderFormsList(forms) {
    const formsList = document.getElementById('formsList');
    if (!formsList) return;

    formsList.innerHTML = '';

    forms.forEach(form => {
        const formCard = createFormCard(form);
        formsList.appendChild(formCard);
    });
}

function createFormCard(form) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-3';

    col.innerHTML = `
        <div class="card h-100">
            <div class="card-body">
                <h6 class="card-title">${form.title || 'Formulário'}</h6>
                <p class="card-text small text-muted">
                    ID: ${form.id}<br>
                    Tipo: ${form.type || 'N/A'}<br>
                    Criado: ${form.created_at || 'N/A'}
                </p>
                <div class="d-flex gap-2">
                    <a href="/form/${form.id}" target="_blank" class="btn btn-primary btn-sm">
                        <i data-feather="external-link"></i> Abrir
                    </a>
                    <button class="btn btn-danger btn-sm" onclick="deleteForm('${form.id}')">
                        <i data-feather="trash-2"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    return col;
}

function deleteForm(formId) {
    if (confirm('Tem certeza que deseja excluir este formulário?')) {
        fetch(`/api/forms/${formId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Erro ao excluir formulário: ' + data.error);
            } else {
                alert('Formulário excluído com sucesso!');
                loadForms(); // Reload the forms list
            }
        })
        .catch(error => {
            console.error('Error deleting form:', error);
            alert('Erro ao excluir formulário');
        });
    }
}

function copyConfigToClipboard(jsonString) {
    // Try to copy to clipboard
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(jsonString).then(() => {
            console.log('config.json copiado para área de transferência!');
        }).catch(err => {
            console.error('Erro ao copiar para área de transferência:', err);
            fallbackCopyToClipboard(jsonString);
        });
    } else {
        fallbackCopyToClipboard(jsonString);
    }
}

function fallbackCopyToClipboard(text) {
    // Fallback method for copying to clipboard
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        console.log('config.json copiado para área de transferência!');
    } catch (err) {
        console.error('Erro ao copiar:', err);
        // Show the JSON in a modal/alert as last resort
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border: 2px solid #ccc;
            border-radius: 10px;
            max-width: 80vw;
            max-height: 80vh;
            overflow: auto;
            z-index: 9999;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;

        modal.innerHTML = `
            <h3>Copie o JSON abaixo:</h3>
            <textarea readonly style="width: 100%; height: 400px; font-family: monospace; font-size: 12px;">${text}</textarea>
            <br><br>
            <button onclick="this.parentElement.remove()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Fechar</button>
        `;

        document.body.appendChild(modal);
    }

    document.body.removeChild(textArea);
}

function switchTab(tabName) {
    console.log('Switching to tab:', tabName);

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Hide all config forms
    document.querySelectorAll('.config-form').forEach(form => {
        form.classList.remove('active');
        form.style.display = 'none';
    });

    // Add active class to clicked tab button
    const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }

    // Show corresponding config form
    const targetForm = document.getElementById(`${tabName}-config`);
    if (targetForm) {
        targetForm.classList.add('active');
        targetForm.style.display = 'block';
        console.log('Showing form:', targetForm.id);
    } else {
        console.error('Target form not found:', `${tabName}-config`);
    }
}

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, initializing admin interface...');
        initializeAdminInterface();
    });
} else {
    console.log('DOM already ready, initializing admin interface...');
    initializeAdminInterface();
}

function getAllYesNoQuestions(formType) {
    // Get current questions for the specific form type
    const currentQuestions = getCurrentQuestions(formType);
    const yesNoQuestions = currentQuestions.filter(q => q.type === 'yesno');
    return yesNoQuestions;
}

//Add conditional questions
function createQuestionElement(formType, question, index) {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-item mb-4 p-3 border rounded';
    questionDiv.setAttribute('data-question-id', question.id);

    let questionHtml = '';

    if (question.type === 'divider') {
        questionHtml = `
            <div class="divider-question">
                <h5 class="text-primary">
                    <i data-feather="minus"></i>
                    ${question.title || 'Divisor'}
                </h5>
                <div class="row">
                    <div class="col-md-8">
                        <label class="form-label">Título do Divisor:</label>
                        <input type="text" class="form-control" value="${question.title || ''}" 
                               onchange="updateQuestionField('${formType}', ${index}, 'title', this.value)">
                    </div>
                    <div class="col-md-4 d-flex align-items-end">
                        <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion('${formType}', ${index})">
                            <i data-feather="trash-2"></i> Remover
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        const typeOptions = {
            'text': 'Texto',
            'longtext': 'Texto Longo',
            'yesno': 'Sim/Não',
            'rating': 'Avaliação (1-10)',
            'dropdown': 'Lista Suspensa',
            'monday_column': 'Coluna Monday'
        };

        questionHtml = `
            <div class="regular-question">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">Pergunta ${index + 1}</h6>
                    <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion('${formType}', ${index})">
                        <i data-feather="trash-2"></i> Remover
                    </button>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Tipo:</label>
                        <select class="form-control" onchange="updateQuestionField('${formType}', ${index}, 'type', this.value)">
                            ${Object.entries(typeOptions).map(([value, text]) => 
                                `<option value="${value}" ${question.type === value ? 'selected' : ''}>${text}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Obrigatória:</label>
                        <select class="form-control" onchange="updateQuestionField('${formType}', ${index}, 'required', this.value === 'true')">
                            <option value="false" ${!question.required ? 'selected' : ''}>Não</option>
                            <option value="true" ${question.required ? 'selected' : ''}>Sim</option>
                        </select>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Texto da Pergunta:</label>
                        <textarea class="form-control" rows="2" 
                                  onchange="updateQuestionField('${formType}', ${index}, 'text', this.value)">${question.text || ''}</textarea>
                    </div>
                </div>

                ${question.type === 'dropdown' ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Opções (separadas por ponto e vírgula):</label>
                        <input type="text" class="form-control" value="${question.dropdown_options || ''}"
                               placeholder="Opção 1;Opção 2;Opção 3"
                               onchange="updateQuestionField('${formType}', ${index}, 'dropdown_options', this.value)">
                    </div>
                </div>
                ` : ''}

                ${question.type === 'monday_column' ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <label class="form-label">Coluna de Origem (Monday):</label>
                        <input type="text" class="form-control" value="${question.source_column || ''}"
                               placeholder="Ex: text_mkrj9z52, dropdown_mksd123"
                               onchange="updateQuestionField('${formType}', ${index}, 'source_column', this.value)">
                        <small class="form-text text-muted">ID da coluna do Monday.com que será usada como nome/valor da pergunta</small>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino - Texto:</label>
                        <input type="text" class="form-control" value="${question.text_destination_column || question.destination_column || ''}"
                               placeholder="Ex: text_mkhotel_name"
                               onchange="updateQuestionField('${formType}', ${index}, 'text_destination_column', this.value)">
                        <small class="form-text text-muted">Onde salvar o nome/texto do item</small>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino - Avaliação:</label>
                        <input type="text" class="form-control" value="${question.rating_destination_column || ''}"
                               placeholder="Ex: numeric_mkrjpfxv"
                               onchange="updateQuestionField('${formType}', ${index}, 'rating_destination_column', this.value)">
                        <small class="form-text text-muted">Onde salvar a nota (1-10)</small>
                    </div>
                </div>
                ` : `
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Coluna de Destino (Monday):</label>
                        <input type="text" class="form-control" value="${question.destination_column || ''}"
                               placeholder="Ex: text_mksd123"
                               onchange="updateQuestionField('${formType}', ${index}, 'destination_column', this.value)">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">ID da Pergunta:</label>
                        <input type="text" class="form-control" value="${question.id || ''}" readonly>
                    </div>
                </div>
                `}

                ${question.type !== 'monday_column' ? `
                <div class="row mt-3">
                    <div class="col-md-6"></div>
                    <div class="col-md-6">
                        <label class="form-label">ID da Pergunta:</label>
                        <input type="text" class="form-control" value="${question.id || ''}" readonly>
                    </div>
                </div>
                ` : ''}

                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Depende da pergunta (Sim/Não):</label>
                        <select class="form-control conditional-depends-on" onchange="updateQuestionConditional('${formType}', ${index}, 'depends_on', this.value)">
                            <option value="">Nenhuma</option>
                            ${getAllYesNoQuestions(formType).map(q => 
                                `<option value="${q.id}" ${question.conditional && question.conditional.depends_on === q.id ? 'selected' : ''}>${q.text || q.id}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Mostrar se a resposta for:</label>
                        <select class="form-control conditional-show-if" onchange="updateQuestionConditional('${formType}', ${index}, 'show_if', this.value)">
                            <option value="">Qualquer resposta</option>
                            <option value="Sim" ${question.conditional && question.conditional.show_if === 'Sim' ? 'selected' : ''}>Sim</option>
                            <option value="Não" ${question.conditional && question.conditional.show_if === 'Não' ? 'selected' : ''}>Não</option>
                        </select>
                    </div>
                </div>

                ${question.conditional ? `
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <strong>Pergunta Condicional:</strong> Depende de "${question.conditional.depends_on}"
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    questionDiv.innerHTML = questionHtml;
    return questionDiv;
}

function updateQuestionConditional(formType, index, field, value) {
    const currentQuestions = getCurrentQuestions(formType);
    if (currentQuestions[index]) {
        if (!currentQuestions[index].conditional) {
            currentQuestions[index].conditional = {};
        }
        currentQuestions[index].conditional[field] = value;
    }
}

// Manual item creation function
function createManualItem() {
    const itemName = document.getElementById('manual-item-name').value.trim();
    const formType = document.getElementById('manual-form-type').value;
    const columnValuesText = document.getElementById('manual-column-values').value.trim();
    const resultDiv = document.getElementById('manual-create-result');

    // Validate inputs
    if (!itemName) {
        showResult(resultDiv, 'error', 'Por favor, digite o nome do item.');
        return;
    }

    if (!formType) {
        showResult(resultDiv, 'error', 'Por favor, selecione o tipo de formulário.');
        return;
    }

    if (!columnValuesText) {
        showResult(resultDiv, 'error', 'Por favor, cole os valores das colunas.');
        return;
    }

    // Parse column values (handle both single and double quotes)
    let columnValues;
    try {
        // Replace single quotes with double quotes for valid JSON
        const jsonText = columnValuesText.replace(/'/g, '"');
        columnValues = JSON.parse(jsonText);
    } catch (e) {
        showResult(resultDiv, 'error', 'Formato JSON inválido. Verifique os valores das colunas. Erro: ' + e.message);
        return;
    }

    // Show loading state
    const createBtn = document.getElementById('createManualItem');
    const originalBtnText = createBtn.innerHTML;
    createBtn.disabled = true;
    createBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Criando...';

    // Send request to create item
    fetch('/api/create-manual-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_name: itemName,
            form_type: formType,
            column_values: columnValues
        })
    })
    .then(response => response.json())
    .then(data => {
        createBtn.disabled = false;
        createBtn.innerHTML = originalBtnText;

        if (data.success) {
            showResult(resultDiv, 'success', `Item criado com sucesso! ID: ${data.item_id}`);
            // Clear form
            document.getElementById('manual-item-name').value = '';
            document.getElementById('manual-column-values').value = '';
        } else {
            showResult(resultDiv, 'error', 'Erro ao criar item: ' + (data.error || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        createBtn.disabled = false;
        createBtn.innerHTML = originalBtnText;
        showResult(resultDiv, 'error', 'Erro ao criar item: ' + error.message);
    });
}

function showResult(element, type, message) {
    element.className = `alert alert-${type === 'success' ? 'success' : 'danger'}`;
    element.textContent = message;
    element.style.display = 'block';
    
    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}
