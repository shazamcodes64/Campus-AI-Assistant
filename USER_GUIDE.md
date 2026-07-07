# Campus AI Assistant - User Guide

## Welcome! 🎓

The Campus AI Assistant helps you find answers to academic questions quickly using your institution's documents and curated FAQs.

---

## Getting Started

### Accessing the System

1. Open your web browser
2. Navigate to: `http://your-campus-ai-url:8501`
3. You'll see the main interface with a query input box

### System Status

Check the sidebar for system status indicators:
- 📊 **Document Index**: Green ✅ means documents are indexed and searchable
- ❓ **FAQ Database**: Green ✅ means FAQ answers are available
- 🤖 **LLM Service**: Green ✅ means AI generation is working

---

## How to Ask Questions

### Best Practices

✅ **DO:**
- Be specific: "What is the placement eligibility criteria?"
- Use keywords from your courses: "OODP syllabus unit 3"
- Ask one question at a time
- Rephrase if you don't get good results

❌ **DON'T:**
- Ask vague questions: "tell me about stuff"
- Ask multiple unrelated questions together
- Ask about topics outside course materials
- Expect answers about current events or general knowledge

### Question Types That Work Well

#### 1. Course Information
- "What is the syllabus for [course name]?"
- "How many credits is [course name]?"
- "What are the prerequisites for [course]?"
- "What topics are covered in Unit 2?"

#### 2. Evaluation and Grading
- "What is the exam pattern?"
- "How are internal marks calculated?"
- "What is the grading system?"
- "How much does the lab count for?"

#### 3. Policies and Procedures
- "What is the attendance policy?"
- "What is the placement process?"
- "How do I apply for revaluation?"
- "What are the graduation requirements?"

#### 4. Deadlines and Schedules
- "When is the project submission deadline?"
- "What is the exam schedule?"
- "When does registration open?"

---

## Example Queries

### ✅ Good Examples

**Course Content:**
```
Q: What is the OODP syllabus?
Q: Explain the topics in Data Structures Unit 1
Q: What programming languages are taught in first year?
```

**Evaluation:**
```
Q: How are lab marks distributed?
Q: What is the internal assessment breakup?
Q: How much does attendance affect my grade?
```

**Placement:**
```
Q: What is the minimum CGPA for placement?
Q: What is the placement process?
Q: What companies visit for campus recruitment?
```

**Policies:**
```
Q: What happens if I fail a subject?
Q: Can I take a semester break?
Q: What is the attendance requirement?
```

### ❌ Poor Examples (Won't Work)

```
Q: help
Q: what?
Q: tell me everything
Q: weather today
Q: best pizza place
Q: how to cook pasta
```

---

## Understanding Responses

### Response Components

1. **Answer**: The main response to your question
2. **Confidence Score**: How confident the system is (0.0 to 1.0)
3. **Method**: How the answer was generated
   - **FAQ Match**: Direct answer from curated FAQ
   - **Direct Source**: Single highly relevant document chunk
   - **AI Generated**: Synthesized from multiple sources
   - **Source Excerpts**: Relevant excerpts when AI is unavailable
4. **Sources**: Which documents the answer came from

### Confidence Levels

- **0.8 - 1.0**: High confidence - answer is very likely accurate
- **0.6 - 0.8**: Medium confidence - answer is probably correct
- **0.5 - 0.6**: Low confidence - verify with original sources
- **< 0.5**: Very low confidence - question may be out of scope

### When You Get "No Information Found"

This means:
- The topic isn't covered in the indexed documents
- Your question might be too vague
- Try rephrasing with different keywords
- Check if you're asking about the right subject area

---

## Tips for Better Results

### 1. Use Specific Keywords

❌ **Vague**: "How do I pass?"
✅ **Specific**: "What is the minimum passing grade for theory exams?"

### 2. Break Down Complex Questions

❌ **Complex**: "Tell me everything about placement including eligibility, process, companies, and what happens after"
✅ **Simple**: Ask separately:
- "What is the placement eligibility criteria?"
- "What is the placement process?"
- "Which companies visit for recruitment?"

### 3. Use Course Names and Codes

❌ **Generic**: "What's in the programming course?"
✅ **Specific**: "What is the OODP course syllabus?"

### 4. Rephrase If Needed

If you don't get good results, try:
- Different keywords
- More specific terms
- Simpler phrasing
- Breaking into smaller questions

### 5. Check Sources

Always review the sources provided:
- Click on source links to see original documents
- Verify important information (deadlines, requirements)
- Cross-reference with official announcements

---

## Common Use Cases

### Scenario 1: Preparing for Exams

```
1. "What is the exam pattern for [course]?"
2. "What topics are covered in Unit [X]?"
3. "How are marks distributed?"
4. "What is the passing criteria?"
```

### Scenario 2: Planning Your Semester

```
1. "What courses are required in [semester]?"
2. "How many credits do I need?"
3. "What are the lab requirements?"
4. "When is the registration deadline?"
```

### Scenario 3: Understanding Placement

```
1. "What is the minimum CGPA for placement?"
2. "What is the placement process?"
3. "What documents are required?"
4. "When does placement season start?"
```

### Scenario 4: Checking Policies

```
1. "What is the attendance policy?"
2. "What happens if I miss an exam?"
3. "How do I apply for revaluation?"
4. "What is the grade improvement policy?"
```

---

## Troubleshooting

### "I'm not getting relevant answers"

**Try:**
1. Make your question more specific
2. Use exact course names or codes
3. Break complex questions into parts
4. Check if the topic is covered in your documents

### "The system says it's out of scope"

**This means:**
- Your question isn't about course materials
- The topic isn't in the indexed documents
- Try rephrasing or asking a different question

### "Response is too slow"

**Possible reasons:**
- System is processing a complex query
- Multiple users are querying simultaneously
- Wait a few seconds and try again
- If persistent, contact your administrator

### "Sources don't match my question"

**Try:**
1. Rephrase your question with different keywords
2. Be more specific about what you're looking for
3. Check if you're using the correct course name

---

## Privacy and Data

### What Gets Logged

- Your queries (anonymized)
- System responses
- Confidence scores
- Performance metrics

### What Doesn't Get Logged

- Personal identifying information
- IP addresses (in production mode)
- Sensitive personal data

### Data Retention

- Logs are kept for 30 days
- Used only for system improvement
- Not shared with third parties

---

## Limitations

### What the System CAN Do

✅ Answer questions about course content
✅ Provide information from indexed documents
✅ Cite sources for answers
✅ Handle typos and informal language
✅ Work 24/7 without breaks

### What the System CANNOT Do

❌ Answer questions outside course materials
❌ Provide real-time information (current events, weather)
❌ Make decisions for you (which course to take)
❌ Replace official academic advisors
❌ Guarantee 100% accuracy (always verify important info)

---

## Best Practices Summary

1. **Be Specific**: Use clear, specific questions
2. **Use Keywords**: Include course names, topics, terms
3. **One at a Time**: Ask one question per query
4. **Check Sources**: Always review provided sources
5. **Verify Important Info**: Cross-check critical information
6. **Rephrase if Needed**: Try different wording
7. **Report Issues**: Let administrators know about problems

---

## Example Session

Here's a typical successful interaction:

**User**: "What is the OODP syllabus?"

**System Response**:
```
Answer: The Object-Oriented Design and Programming (OODP) course 
covers the following topics:

Unit 1: Introduction to OOP concepts, classes, objects, encapsulation
Unit 2: Inheritance, polymorphism, abstract classes
Unit 3: Exception handling, file I/O
Unit 4: Collections framework, generics
Unit 5: Design patterns, SOLID principles

Confidence: 0.92
Method: AI Generated
Sources:
1. OODP Syllabus.pdf (page 2)
2. common-courses-syllabus.pdf (page 15)
```

**User**: "How many credits is this course?"

**System Response**:
```
Answer: OODP is a 4-credit course with 3 hours of theory 
and 2 hours of lab per week.

Confidence: 0.88
Method: Direct Source
Sources:
1. OODP Syllabus.pdf (page 1)
```

---

## Getting Help

### If You Need Assistance

1. **Check this guide** for common questions
2. **Try rephrasing** your question
3. **Contact your instructor** for academic advice
4. **Report technical issues** to IT support

### Feedback

Help us improve! If you:
- Find incorrect information
- Have suggestions for better responses
- Encounter technical problems
- Want additional features

Please report to your system administrator.

---

## Quick Reference Card

### Query Formula
```
[Action] + [Specific Topic] + [Context]

Examples:
"What is" + "the attendance policy" + "for lab courses"
"How many" + "credits" + "for OODP"
"When is" + "the project deadline" + "for Data Structures"
```

### Response Checklist
- [ ] Answer makes sense
- [ ] Confidence is reasonable (>0.6)
- [ ] Sources are relevant
- [ ] Information matches your question

### When to Verify
- ⚠️ Confidence < 0.6
- ⚠️ Important deadlines or requirements
- ⚠️ Grade-related information
- ⚠️ Policy decisions

---

## Frequently Asked Questions

**Q: Can I ask questions in my native language?**
A: Currently, the system works best with English queries.

**Q: How often is the information updated?**
A: Documents are indexed when added. FAQ can be updated anytime.

**Q: What if the answer contradicts what my professor said?**
A: Always defer to your professor. The system provides information from documents, but professors have the final say.

**Q: Can I use this for exam preparation?**
A: Yes! It's great for reviewing syllabus, topics, and policies. But don't rely solely on it - use your textbooks and notes too.

**Q: Why does it sometimes say "LLM service unavailable"?**
A: The AI generation service might be temporarily down. You'll still get relevant document excerpts.

**Q: Can I save my queries and responses?**
A: Currently, no. Take screenshots or notes if you need to save information.

---

## Success Tips from Students

💡 **"I use it to quickly check syllabus topics before exams"**

💡 **"Great for understanding placement process without reading the entire handbook"**

💡 **"Helps me find specific information in long PDF documents"**

💡 **"I always verify important dates with the official calendar, but it's a good starting point"**

💡 **"Works best when I'm specific about what I'm looking for"**

---

## Remember

The Campus AI Assistant is a tool to help you find information faster. It's not a replacement for:
- Reading course materials
- Attending classes
- Consulting with professors
- Official academic advisors
- Your own judgment and critical thinking

Use it wisely, verify important information, and happy learning! 🎓
