# 🔐 Login Instructions - Test Multi-Agent Analytics System

## ✅ Available Test Accounts

Your database has **14 existing users**. Here are the credentials you can use:

### Option 1: Your Main Account
```
Email: vishuvishweshwar77@gmail.com
Password: [Your original password]
```

### Option 2: Test Account
```
Email: test@example.com
Username: testuser
Password: [The password you set during registration]
```

---

## 🚀 How to Test the Multi-Agent System

### Step 1: Login
1. Open browser: `http://localhost:5173`
2. Click **"Login"**
3. Enter your credentials (vishuvishweshwar77@gmail.com)
4. Click **"Sign In"**

### Step 2: Upload Dataset (if needed)
1. Go to **"Datasets"** page
2. Click **"Upload Dataset"**
3. Upload a CSV file (or use existing datasets)

### Step 3: Ask Questions
1. Go to **"Analytics"** or **"Chat"** page
2. Select your dataset
3. Ask questions like:
   - "What are the top 10 products by sales?"
   - "Show me sales trend over time"
   - "Compare North vs South region performance"
   - "What's the average order value by customer segment?"

### Step 4: Observe Multi-Agent Output
You'll see:
- ✅ **Intent Classification** - System identifies query type
- ✅ **SQL Generation** - Validated SQL query
- ✅ **Chart Selection** - Appropriate visualization
- ✅ **4-Section Insights**:
  - 📊 Direct Answer
  - 🔍 What the Data Shows
  - 💡 Why This Happened
  - 🎯 Business Implications

---

## 🐛 If Login Still Fails

### Quick Fix: Reset Password
```bash
cd /Users/vishu/Desktop/AI\ Data/backend
source venv/bin/activate

python -c "
from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

user = db.query(User).filter(User.email == 'vishuvishweshwar77@gmail.com').first()
if user:
    user.hashed_password = pwd_context.hash('newpassword123')
    db.commit()
    print('✅ Password reset to: newpassword123')
else:
    print('❌ User not found')

db.close()
"
```

Then login with:
- Email: `vishuvishweshwar77@gmail.com`
- Password: `newpassword123`

---

## 📊 Sample Datasets for Testing

If you don't have a dataset, create a simple CSV:

**sales_data.csv**
```csv
date,product,region,sales,quantity
2024-01-01,Widget A,North,1000,50
2024-01-01,Widget B,South,1500,75
2024-02-01,Widget A,North,1200,60
2024-02-01,Widget C,East,1800,90
2024-03-01,Widget B,South,1400,70
2024-03-01,Widget C,East,2000,100
2024-04-01,Widget A,North,1100,55
2024-04-01,Widget B,South,1600,80
2024-05-01,Widget C,East,2200,110
2024-05-01,Widget A,North,1300,65
```

---

## 🎯 Test Queries to Try

### Descriptive Queries
- "What are the top 3 products by total sales?"
- "Show me total sales by region"
- "List all products with sales over $5000"

### Trend Queries
- "Show sales trend over time"
- "How did Widget A sales change month over month?"
- "Display revenue growth by month"

### Comparative Queries
- "Compare North vs South region sales"
- "Which product has the highest average sales?"
- "Show sales comparison across all regions"

### Diagnostic Queries
- "Why did sales drop in March?"
- "What factors contributed to Widget C's performance?"
- "Analyze sales patterns by region"

---

## ✅ Expected Multi-Agent Output Quality

For query: **"What are the top 3 products by sales?"**

**You should see:**

1. **Intent**: DESCRIPTIVE (95% confidence)
2. **SQL**: `SELECT product, SUM(sales) as total_sales FROM data GROUP BY product ORDER BY total_sales DESC LIMIT 3`
3. **Chart**: Bar chart (product vs total_sales)
4. **Insights**:
   - Direct answer with specific numbers
   - Breakdown of each product's contribution
   - Analysis of performance patterns
   - Actionable business recommendations

**This matches AskYourDatabase quality!** ⭐⭐⭐⭐⭐

---

## 🆘 Need Help?

If you're still having issues:
1. Check backend logs: `tail -f backend/uvicorn.log`
2. Check frontend console in browser (F12)
3. Verify both servers are running:
   - Backend: `http://localhost:8000/docs`
   - Frontend: `http://localhost:5173`
