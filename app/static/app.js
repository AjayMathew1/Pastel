document.addEventListener('DOMContentLoaded', () => {
	const quickButtons = document.querySelectorAll('.quick-add .btn[data-mins]');
	const durationInput = document.querySelector('input[name="duration_minutes"]');
	quickButtons.forEach(btn => {
		btn.addEventListener('click', () => {
			const inc = parseInt(btn.getAttribute('data-mins') || '0', 10);
			const curr = parseInt(durationInput.value || '0', 10);
			durationInput.value = Math.min(1440, curr + inc).toString();
		});
	});

	// Simple pie chart renderer (no external deps)
	const canvas = document.getElementById('pie');
	if (canvas && window['PIE_DATA']) {
		const ctx = canvas.getContext('2d');
		const items = window['PIE_DATA']; // [[label, value], ...]
		const total = items.reduce((s, x) => s + (x[1] || 0), 0) || 1;
		const centerX = canvas.width / 2;
		const centerY = canvas.height / 2;
		const radius = Math.min(centerX, centerY) - 10;
		let startAngle = -Math.PI / 2;
		const pastel = [
			'#E6E0FF','#DFF5E1','#FFE3E3','#E0F2FF','#FFF4D6','#FDE2FF','#D1F1FF','#FFE8CC'
		];
		items.forEach((item, idx) => {
			const value = item[1] || 0;
			const sliceAngle = (value / total) * Math.PI * 2;
			ctx.beginPath();
			ctx.moveTo(centerX, centerY);
			ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
			ctx.closePath();
			ctx.fillStyle = pastel[idx % pastel.length];
			ctx.fill();
			// labels
			const mid = startAngle + sliceAngle / 2;
			const lx = centerX + Math.cos(mid) * (radius * 0.65);
			const ly = centerY + Math.sin(mid) * (radius * 0.65);
			ctx.fillStyle = '#1f2937';
			ctx.font = '12px Inter, sans-serif';
			const label = `${item[0]} ${(value/total*100).toFixed(0)}%`;
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText(label, lx, ly);
			startAngle += sliceAngle;
		});

		// Legend
		const legend = document.getElementById('legend');
		if (legend) {
			legend.innerHTML = '';
			items.forEach((item, idx) => {
				const value = item[1] || 0;
				const pct = ((value/total)*100).toFixed(0);
				const row = document.createElement('div');
				row.style.display = 'flex';
				row.style.alignItems = 'center';
				row.style.marginBottom = '6px';
				const swatch = document.createElement('span');
				swatch.style.width = '12px';
				swatch.style.height = '12px';
				swatch.style.borderRadius = '3px';
				swatch.style.marginRight = '8px';
				swatch.style.background = pastel[idx % pastel.length];
				const text = document.createElement('span');
				text.textContent = `${item[0]} — ${value} min (${pct}%)`;
				row.appendChild(swatch);
				row.appendChild(text);
				legend.appendChild(row);
			});
		}
	}
});


