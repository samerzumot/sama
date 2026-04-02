const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { priceId, packageName } = req.body;

  // Define prices based on package name
  // Note: For a production app, these should be official Price IDs from the Stripe Dashboard.
  // For now, I'll use ad-hoc line items.
  let amount = 0;
  let description = '';

  if (packageName === 'basic') {
    amount = 1000; // $10.00
    description = '20 Minutes of AI Tutoring';
  } else if (packageName === 'standard') {
    amount = 2500; // $25.00
    description = '60 Minutes of AI Tutoring';
  } else if (packageName === 'pro') {
    amount = 4500; // $45.00
    description = 'Pro Tier (60 minutes included, $0.40/min after)';
  } else {
    return res.status(400).json({ error: 'Invalid package' });
  }

  try {
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: description,
            },
            unit_amount: amount,
            recurring: { interval: 'month' },
          },
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: `${req.headers.origin}/success.html?session_id={CHECKOUT_SESSION_ID}&package=${packageName}`,
      cancel_url: `${req.headers.origin}/cancel.html`,
    });

    res.status(200).json({ id: session.id });
  } catch (error) {
    console.error('Stripe Error:', error);
    res.status(500).json({ error: error.message });
  }
};
