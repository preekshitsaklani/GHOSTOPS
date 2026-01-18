/**
 * ClarityOS Widget Loader v3.0
 * Features: Chat, File Upload, Document Preview, Mentor Hover Tooltips
 */

(function () {
    const API_URL = "http://localhost:8000";
    const PRIMARY_COLOR = "#2563EB";

    const style = document.createElement('style');
    style.textContent = `
        #clarity-widget-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: 'Inter', sans-serif; }
        #clarity-launcher { background: ${PRIMARY_COLOR}; width: 60px; height: 60px; border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
        #clarity-launcher:hover { transform: scale(1.05); }
        #clarity-window { display: none; width: 420px; height: 700px; background: #fff; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); flex-direction: column; overflow: hidden; position: absolute; bottom: 80px; right: 0; }
        .clarity-header { background: ${PRIMARY_COLOR}; padding: 16px; color: white; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
        .clarity-body { flex: 1; padding: 16px; overflow-y: auto; background: #F9FAFB; display: flex; flex-direction: column; gap: 12px; }
        .clarity-input-area { padding: 12px; border-top: 1px solid #E5E7EB; background: #fff; display: flex; flex-direction: column; gap: 8px; }
        .clarity-input-row { display: flex; gap: 8px; align-items: center; }
        .clarity-input { flex: 1; border: 1px solid #D1D5DB; border-radius: 20px; padding: 8px 16px; outline: none; }
        .msg { padding: 10px 14px; border-radius: 12px; max-width: 90%; font-size: 14px; line-height: 1.5; white-space: pre-wrap; }
        .msg-assistant { background: #fff; border: 1px solid #E5E7EB; color: #1F2937; align-self: flex-start; }
        .msg-user { background: ${PRIMARY_COLOR}; color: white; align-self: flex-end; }
        
        /* Mentor Card with Tooltip */
        .mentor-card { 
            background: white; border: 1px solid #E5E7EB; border-radius: 8px; 
            padding: 12px; margin-top: 8px; cursor: pointer; 
            transition: all 0.3s ease; position: relative;
        }
        .mentor-card:hover { 
            border-color: ${PRIMARY_COLOR}; 
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
        }
        .mentor-name { font-weight: 700; color: #111827; }
        .mentor-bio { font-size: 12px; color: #6B7280; margin: 4px 0; }
        .mentor-outcome { font-size: 11px; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; display: inline-block; font-weight: 600; }
        
        /* Tooltip */
        .mentor-tooltip {
            position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%);
            background: #1F2937; color: white; padding: 10px 14px;
            border-radius: 8px; font-size: 12px; line-height: 1.4;
            width: 250px; opacity: 0; visibility: hidden;
            transition: all 0.2s ease; z-index: 100;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .mentor-tooltip::after {
            content: ''; position: absolute; top: 100%; left: 50%;
            transform: translateX(-50%); border: 6px solid transparent;
            border-top-color: #1F2937;
        }
        .mentor-card:hover .mentor-tooltip { opacity: 1; visibility: visible; }
        
        /* Document Preview */
        .doc-preview {
            background: #FFFBEB; border: 1px solid #FCD34D;
            border-radius: 8px; padding: 12px; font-size: 12px;
            font-family: monospace; white-space: pre-wrap;
            max-height: 300px; overflow-y: auto;
        }
        
        /* Review Buttons */
        .review-buttons { display: flex; gap: 8px; margin-top: 8px; }
        .review-btn {
            padding: 8px 16px; border-radius: 20px; cursor: pointer;
            font-size: 13px; font-weight: 600; border: none;
            transition: all 0.2s;
        }
        .review-btn.approve { background: #10B981; color: white; }
        .review-btn.approve:hover { background: #059669; }
        .review-btn.edit { background: #F3F4F6; color: #374151; }
        .review-btn.edit:hover { background: #E5E7EB; }
        
        .file-badge { display: none; align-items: center; gap: 6px; padding: 6px 10px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; font-size: 12px; color: ${PRIMARY_COLOR}; }
        .file-badge.active { display: flex; }
        .file-badge .remove { cursor: pointer; font-weight: bold; margin-left: 4px; }
        .upload-btn { cursor: pointer; padding: 4px 8px; background: #F3F4F6; border-radius: 8px; font-size: 18px; }
        .upload-btn:hover { background: #E5E7EB; }
        
        /* Document Saved Badge */
        .doc-saved { 
            background: #10B981; color: white; padding: 8px 12px; 
            border-radius: 8px; font-size: 12px; display: inline-flex;
            align-items: center; gap: 6px; margin: 8px 0;
        }
    `;
    document.head.appendChild(style);

    const container = document.createElement('div');
    container.id = 'clarity-widget-container';
    container.innerHTML = `
        <div id="clarity-window">
            <div class="clarity-header">
                <span>⚡ ClarityOS</span>
                <span id="clarity-close" style="cursor:pointer;">✕</span>
            </div>
            <div class="clarity-body" id="clarity-messages">
                <div class="msg msg-assistant">Hi! I'm ClarityOS. I'll help you find the perfect mentor. Let's start by understanding your challenge. 📎 You can upload documents for better analysis.</div>
            </div>
            <div class="clarity-input-area">
                <div id="file-badge" class="file-badge">
                    <span>📄 <span id="file-name">file.pdf</span></span>
                    <span class="remove" id="remove-file">×</span>
                </div>
                <div class="clarity-input-row">
                    <label for="file-upload" class="upload-btn">📎</label>
                    <input type="file" id="file-upload" style="display:none;" accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx,.xls,.ppt,.pptx" />
                    <input type="text" id="clarity-input" class="clarity-input" placeholder="Describe your challenge..." />
                    <button id="clarity-send" style="background:none; border:none; cursor:pointer; font-size:20px;">🚀</button>
                </div>
            </div>
        </div>
        <div id="clarity-launcher">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
        </div>
    `;
    document.body.appendChild(container);

    const launcher = document.getElementById('clarity-launcher');
    const windowEl = document.getElementById('clarity-window');
    const closeBtn = document.getElementById('clarity-close');
    const input = document.getElementById('clarity-input');
    const sendBtn = document.getElementById('clarity-send');
    const msgContainer = document.getElementById('clarity-messages');
    const fileUpload = document.getElementById('file-upload');
    const fileBadge = document.getElementById('file-badge');
    const fileNameEl = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');

    let history = [];
    let currentFileContext = null;

    const toggleWindow = () => {
        windowEl.style.display = windowEl.style.display === 'flex' ? 'none' : 'flex';
    };

    const addMessage = (text, role) => {
        const div = document.createElement('div');
        div.className = `msg msg-${role}`;
        div.innerHTML = text;
        msgContainer.appendChild(div);
        msgContainer.scrollTop = msgContainer.scrollHeight;
        history.push({ role: role, content: text });
    };

    const addMentorCard = (mentor) => {
        const div = document.createElement('div');
        div.className = 'mentor-card';
        const reason = mentor.why_this_mentor || `Expert in ${mentor.bio?.split('.')[0]}`;
        div.innerHTML = `
            <div class="mentor-tooltip">💡 <strong>Why this mentor?</strong><br>${reason}</div>
            <div class="mentor-name">${mentor.name}</div>
            <div class="mentor-bio">${mentor.bio}</div>
            <div class="mentor-outcome">🏆 ${mentor.outcomes}</div>
        `;
        div.onclick = () => window.open(mentor.link || "#", '_blank');
        msgContainer.appendChild(div);
        msgContainer.scrollTop = msgContainer.scrollHeight;
    };

    const addDocumentSavedBadge = (path) => {
        const div = document.createElement('div');
        div.className = 'doc-saved';
        div.innerHTML = `✅ Document saved: <strong>${path.split('/').pop()}</strong>`;
        msgContainer.appendChild(div);
        msgContainer.scrollTop = msgContainer.scrollHeight;
    };

    // File Upload Handler
    fileUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        addMessage(`📤 Uploading ${file.name}...`, 'user');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                currentFileContext = data.content;
                fileNameEl.textContent = file.name;
                fileBadge.classList.add('active');
                addMessage(`✅ <b>${file.name}</b> analyzed! I'll use this context in our chat.`, 'assistant');
            } else {
                addMessage(`❌ Upload failed: ${data.detail || 'Unknown error'}`, 'assistant');
            }
        } catch (err) {
            console.error(err);
            addMessage("❌ Upload failed. Check if backend is running.", 'assistant');
        }
    });

    removeFileBtn.addEventListener('click', () => {
        currentFileContext = null;
        fileBadge.classList.remove('active');
        fileUpload.value = '';
    });

    const handleSend = async () => {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';

        try {
            const res = await fetch(`${API_URL}/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    history: history,
                    file_context: currentFileContext
                })
            });
            const data = await res.json();

            addMessage(data.reply, 'assistant');

            // Show document saved badge
            if (data.document_saved && data.document_path) {
                addDocumentSavedBadge(data.document_path);
            }

            // Show mentor cards with tooltips
            if (data.cards && data.cards.length > 0) {
                data.cards.forEach(addMentorCard);
            }
        } catch (err) {
            console.error(err);
            addMessage("⚠️ ClarityOS is offline. Please check backend.", "assistant");
        }
    };

    launcher.addEventListener('click', toggleWindow);
    closeBtn.addEventListener('click', toggleWindow);
    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keypress', (e) => e.key === 'Enter' && handleSend());

})();
