# 🌐 Hevy Coach Web App Concept

## 🎯 **Vision: One-Click Hevy Coaching**

Transform from "technical setup required" to "sign up and get daily coaching emails in 2 minutes"

## 🏗️ **Recommended Architecture: Vercel + Supabase**

### **Tech Stack:**
- **Frontend**: Next.js 14 (React) on Vercel
- **Database**: Supabase (PostgreSQL) 
- **Auth**: Supabase Auth
- **Cron Jobs**: Vercel Cron Functions
- **Email**: Resend.com API
- **Analytics**: Vercel Analytics

### **User Flow:**
```
1. Visit: hevy-coach.app
2. Sign up with email
3. Enter Hevy API key
4. Configure email preferences (time, timezone)
5. Get daily coaching emails automatically
```

### **Database Schema:**
```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  timezone TEXT DEFAULT 'UTC',
  email_time TIME DEFAULT '08:00',
  is_active BOOLEAN DEFAULT true
);

-- User settings
CREATE TABLE user_settings (
  user_id UUID REFERENCES users(id),
  hevy_api_key TEXT ENCRYPTED NOT NULL,
  notification_email TEXT,
  frequency TEXT DEFAULT 'daily', -- daily, weekly, manual
  rep_targets JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Reports history (optional)
CREATE TABLE report_history (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  generated_at TIMESTAMP DEFAULT NOW(),
  session_grade TEXT,
  exercises_analyzed INTEGER,
  email_sent BOOLEAN DEFAULT false
);
```

## 🔧 **Technical Implementation**

### **1. Frontend Components:**

#### **Landing Page** (`pages/index.js`)
```jsx
export default function Landing() {
  return (
    <div className="hero">
      <h1>🏋️‍♂️ Your AI Fitness Coach</h1>
      <p>Get personalized workout analysis from your Hevy data</p>
      
      <div className="demo-email">
        📧 Preview: "A+ Session! Increase bench to 85kg next time"
      </div>
      
      <SignUpButton />
    </div>
  )
}
```

#### **Dashboard** (`pages/dashboard.js`)
```jsx
export default function Dashboard({ user }) {
  return (
    <div className="dashboard">
      <h2>⚙️ Your Coaching Settings</h2>
      
      <ApiKeyInput 
        value={user.hevy_api_key}
        onSave={updateApiKey}
      />
      
      <EmailSchedule
        timezone={user.timezone}
        time={user.email_time}
        onUpdate={updateSchedule}
      />
      
      <RepTargetsEditor
        targets={user.rep_targets}
        onSave={updateTargets}
      />
      
      <RecentReports reports={user.recent_reports} />
    </div>
  )
}
```

### **2. Serverless Functions:**

#### **Daily Report Generator** (`api/cron/daily-reports.js`)
```javascript
import { analyzeUserWorkouts, sendCoachingEmail } from '@/lib/hevy-coach'
import { getActiveUsers } from '@/lib/database'

export default async function handler(req, res) {
  // Verify cron secret
  if (req.headers.authorization !== `Bearer ${process.env.CRON_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' })
  }
  
  const users = await getActiveUsers()
  const results = []
  
  for (const user of users) {
    try {
      // Check if it's the right time for this user's timezone
      if (!isTimeToSendReport(user)) continue
      
      // Generate personalized report
      const report = await analyzeUserWorkouts(user.hevy_api_key)
      
      // Send email
      await sendCoachingEmail(user.email, report)
      
      results.push({ userId: user.id, status: 'sent' })
    } catch (error) {
      results.push({ userId: user.id, status: 'error', error: error.message })
    }
  }
  
  res.json({ processed: results.length, results })
}
```

#### **Manual Report** (`api/generate-report.js`)
```javascript
export default async function handler(req, res) {
  const { user } = await authenticateUser(req)
  
  try {
    const report = await analyzeUserWorkouts(user.hevy_api_key)
    
    // Option 1: Return report data for web display
    if (req.query.format === 'web') {
      return res.json({ report })
    }
    
    // Option 2: Send email immediately
    await sendCoachingEmail(user.email, report)
    res.json({ success: true, message: 'Report sent to your email!' })
    
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
}
```

### **3. Vercel Configuration:**

#### **vercel.json**
```json
{
  "crons": [
    {
      "path": "/api/cron/daily-reports",
      "schedule": "0 * * * *"
    }
  ],
  "env": {
    "CRON_SECRET": "@cron-secret",
    "SUPABASE_URL": "@supabase-url",
    "SUPABASE_KEY": "@supabase-key",
    "RESEND_API_KEY": "@resend-key"
  }
}
```

## 💰 **Cost Analysis:**

### **Vercel Pro ($20/month):**
- ✅ Unlimited serverless functions
- ✅ Cron jobs included
- ✅ 1000 GB bandwidth
- ✅ Custom domains

### **Supabase Pro ($25/month):**
- ✅ 8GB database
- ✅ 100GB bandwidth  
- ✅ Auth included
- ✅ Real-time features

### **Resend ($20/month):**
- ✅ 50,000 emails/month
- ✅ Custom domains
- ✅ Analytics
- ✅ Great deliverability

### **Total: ~$65/month for thousands of users**

## 📈 **Scaling Strategy:**

### **Phase 1: MVP (0-100 users)**
- Basic web signup
- Daily email reports
- Simple dashboard
- **Revenue**: Free tier to build audience

### **Phase 2: Growth (100-1000 users)**
- Premium features (custom rep targets, multiple emails)
- Workout trends analysis
- Mobile-responsive design
- **Revenue**: $5/month premium tier

### **Phase 3: Scale (1000+ users)**
- Advanced analytics dashboard
- Team/coach features
- API for other apps
- **Revenue**: $10/month pro tier, $25/month coach tier

## 🎨 **User Experience Improvements:**

### **Before (Current):**
```
1. Find GitHub repo ❌
2. Fork repository ❌
3. Set up GitHub secrets ❌
4. Configure cron schedule ❌
5. Debug email issues ❌
6. Maintain your fork ❌
```

### **After (Web App):**
```
1. Visit hevy-coach.app ✅
2. Sign up with email ✅
3. Enter Hevy API key ✅
4. Choose email time ✅
5. Get daily coaching! ✅
```

## 🛡️ **Security & Privacy:**

### **Data Encryption:**
```javascript
// Encrypt API keys at rest
const encryptedApiKey = await encrypt(apiKey, process.env.ENCRYPTION_KEY)
await supabase.from('user_settings').insert({
  user_id: user.id,
  hevy_api_key: encryptedApiKey
})
```

### **Privacy Controls:**
- ✅ **Data deletion**: One-click account deletion
- ✅ **Export**: Download all your data
- ✅ **Transparency**: Open source analysis algorithms
- ✅ **Minimal storage**: Only API keys and preferences

## 🚀 **Competitive Advantages:**

### **vs. Manual Scripts:**
- ❌ No setup complexity
- ❌ No technical knowledge required
- ✅ Automatic updates
- ✅ Web dashboard

### **vs. Other Fitness Apps:**
- ✅ Works with existing Hevy data
- ✅ Advanced RPE analysis
- ✅ Personalized coaching
- ✅ Email convenience

## 📱 **Mobile Considerations:**

### **Progressive Web App:**
- 📱 Add to home screen
- 🔔 Push notifications (future)
- 📶 Offline viewing of reports
- 🎨 Mobile-first design

### **Email Optimization:**
- 📧 Mobile-friendly email templates
- 📱 Tap to view full report
- 🔗 Deep links to web dashboard
- 📊 Summary cards for quick reading

## 🎯 **Go-to-Market Strategy:**

### **Launch Sequence:**
1. **Week 1**: Deploy MVP to hevy-coach.app
2. **Week 2**: Post on r/fitness, r/weightroom
3. **Week 3**: Reach out to Hevy community
4. **Week 4**: Product Hunt launch
5. **Month 2**: Add premium features
6. **Month 3**: Partnership discussions with Hevy

### **Content Marketing:**
- 📺 YouTube: "AI Coaching vs Human Coaching"
- 📝 Blog: "The Science of RPE-Based Training"
- 🐦 Twitter: Daily coaching tips and insights
- 📱 TikTok: Quick workout analysis demos 