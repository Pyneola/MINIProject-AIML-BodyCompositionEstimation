document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('est-form');
    const placeholderBox = document.getElementById('placeholder-box');
    const outputBox = document.getElementById('output-box');
    const sourceBadge = document.getElementById('source-badge');
    const valErrorCard = document.getElementById('validation-error');
    const screenBadge = document.getElementById('screen-badge');

    const FIELDS = [
        ['age', 'RIDAGEYR', 'อายุ (ปี)', 18, 59],
        ['weight', 'BMXWT', 'น้ำหนัก (กก.)', 36, 177],
        ['height', 'BMXHT', 'ส่วนสูง (ซม.)', 138, 191],
        ['waist', 'BMXWAIST', 'รอบเอว (ซม.)', 56, 155],
        ['hip', 'BMXHIP', 'รอบสะโพก (ซม.)', 77, 169],
        ['armc', 'BMXARMC', 'รอบต้นแขน (ซม.)', 20, 53],
        ['arml', 'BMXARML', 'ความยาวแขนท่อนบน (ซม.)', 29, 46],
        ['leg', 'BMXLEG', 'ความยาวขาท่อนบน (ซม.)', 26, 50],
    ];
    const ALMI_CUT = { 1: 7.0, 2: 5.5 };

    ['waist', 'hip', 'armc', 'arml', 'leg'].forEach(id => {
        const el = document.getElementById(id), mk = document.querySelector(`.mk[data-for="${id}"]`);
        el.addEventListener('focus', () => mk.classList.add('on'));
        el.addEventListener('blur', () => mk.classList.remove('on'));
    });

    let runId = 0;

    function run(showErrors) {
        valErrorCard.classList.add('hidden');
        valErrorCard.innerHTML = '';
        document.querySelectorAll('input, select').forEach(el => el.classList.remove('input-error'));

        const gender = parseFloat(document.getElementById('gender').value);
        const payload = { RIAGENDR: gender };
        const errors = [];
        FIELDS.forEach(([id, key, label, lo, hi]) => {
            const v = parseFloat(document.getElementById(id).value);
            if (isNaN(v) || v < lo || v > hi) {
                errors.push(`${label} ต้องเป็นตัวเลขระหว่าง ${lo} ถึง ${hi} (ช่วงของข้อมูลที่ใช้สอน)`);
                document.getElementById(id).classList.add('input-error');
            }
            payload[key] = v;
        });
        if (gender !== 1.0 && gender !== 2.0) errors.push('เพศต้องเป็นชายหรือหญิง');

        if (errors.length > 0 && !showErrors) {
            document.querySelectorAll('input, select').forEach(el => el.classList.remove('input-error'));
            return;
        }
        if (errors.length > 0) {
            valErrorCard.classList.remove('hidden');
            let html = '<strong>กรุณาแก้ค่าที่กรอกต่อไปนี้</strong><ul>';
            errors.forEach(err => {
                html += `<li>${err.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</li>`;
            });
            valErrorCard.innerHTML = html + '</ul>';
            valErrorCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            return;
        }

        const myRun = ++runId;
        fetch('http://127.0.0.1:8000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                if (myRun !== runId) return;
                if (data.success) {
                    setBadge('ต่อเซิร์ฟเวอร์แล้ว', true);
                    render({
                        fatPct: data.fatPct, leanKg: data.leanKg, almKg: data.almKg, trunkKg: data.trunkKg,
                        prob: data.screen.LOW_HT2.probability,
                        refer90: data.screen.LOW_HT2.refer_sens90, refer80: data.screen.LOW_HT2.refer_sens80,
                        height: payload.BMXHT, weight: payload.BMXWT, gender, mae: data.testMae
                    });
                } else {
                    serverDown();
                }
            })
            .catch(() => { if (myRun === runId) serverDown(); });
    }

    function serverDown() {
        setBadge('เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณารัน uvicorn server:app ในโฟลเดอร์ app', false);
        outputBox.classList.add('hidden');
        placeholderBox.classList.remove('hidden');
    }

    form.addEventListener('submit', (e) => { e.preventDefault(); run(true); });
    let timer;
    form.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => run(false), 450); });
    run(false);

    function render(r) {
        const almi = r.almKg / Math.pow(r.height / 100, 2);
        const cut = ALMI_CUT[r.gender];
        set('fat-val', `${r.fatPct.toFixed(1)} %`);
        set('lean-val', `${r.leanKg.toFixed(1)} กก.`);
        set('alm-val', `${r.almKg.toFixed(1)} กก.`);
        set('trunk-val', `${r.trunkKg.toFixed(1)} กก.`);
        set('almi-text', almi.toFixed(2));
        set('almi-cut', `เกณฑ์อ้างอิง ถ้าต่ำกว่า ${cut.toFixed(1)} กก./ม² (${r.gender === 1 ? 'ชาย' : 'หญิง'}) ถือว่ามวลกล้ามเนื้อต่ำ`);
        const ALMI_MAX = 12;
        document.getElementById('bar-almi').style.width = `${Math.max(0, Math.min(100, (almi / ALMI_MAX) * 100))}%`;
        document.getElementById('tick-almi').style.left = `${(cut / ALMI_MAX) * 100}%`;

        const flagged = r.refer90;
        let text = flagged ? 'สรุป โมเดลคัดกรองแนะนำให้ตรวจ DXA เพื่อยืนยัน' : 'สรุป ตอนนี้กล้ามเนื้อยังไม่ต่ำกว่าเกณฑ์';
        if (flagged && almi >= cut) text += ' (ดัชนีที่แสดงอยู่ใกล้เกณฑ์ ค่าประมาณคลาดเคลื่อนได้)';
        if (!flagged && almi < cut) text += ' (ดัชนีที่แสดงต่ำกว่าเกณฑ์เล็กน้อย ค่าประมาณคลาดเคลื่อนได้)';
        const color = flagged ? '#d97706' : '#0f766e';
        document.getElementById('heavy-warning').classList.toggle('hidden', !(r.weight > 120));
        screenBadge.textContent = text;
        screenBadge.style.color = color;

        placeholderBox.classList.add('hidden');
        outputBox.classList.remove('hidden');
    }

    function set(id, text) { document.getElementById(id).textContent = text; }

});
