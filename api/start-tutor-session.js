// node-fetch removed to use native fetch available in Node 18+

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { tutorId, userName } = req.body;

  if (tutorId !== 'admissions') {
    return res.status(400).json({ error: 'Tutor not available' });
  }

  const apiKey = process.env.TAVUS_API_KEY;
  const personaId = process.env.TAVUS_PERSONA_ID || 'pcb75935c995'; // Updated persona ID

  if (!apiKey) {
    return res.status(500).json({ error: 'Tavus API Key not configured' });
  }

  try {
    const response = await fetch('https://tavusapi.com/v2/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey
      },
      body: JSON.stringify({
        persona_id: personaId,
        callback_url: `${req.headers.origin}/api/tavus-callback`,
        conversation_name: `Session with ${userName || 'Student'}`,
        properties: {
          max_call_duration: 150,
          participant_left_timeout: 60
        }
      })
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'Failed to create Tavus conversation');
    }

    res.status(200).json({ 
      conversation_url: data.conversation_url,
      conversation_id: data.conversation_id 
    });
  } catch (error) {
    console.error('Tavus Error:', error);
    res.status(500).json({ error: error.message });
  }
};
