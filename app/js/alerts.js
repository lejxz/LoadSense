  async function createAlert(vehicle_id, route, message) {
    try {
      const note = message || prompt(`Describe the incident for ${vehicle_id}`, `${vehicle_id} flagged by operator`);
      if (!note || !confirm(`Create operator incident for ${vehicle_id}?`)) return false;
      const payload = { vehicle_id, route, message: note, severity: 'medium' };
      const response = await fetch(api + '/alerts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (result.alert) {
        await fetch(api + '/operator-feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ alert_id: result.alert.id, vehicle_id, route, action: `created: ${note}` }),
        });
      }
      await refreshData();
      renderOperator();
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  }

