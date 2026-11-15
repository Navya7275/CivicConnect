import type { Conversation, WelfareScheme, LegalAct, Citation } from './api';
import realSchemesData from './realSchemes.json';
import realActsData from './realActs.json';

export const mockConversations: Conversation[] = [];

export const mockWelfareSchemes: WelfareScheme[] = realSchemesData as WelfareScheme[];

export const mockLegalActs: LegalAct[] = realActsData as LegalAct[];

// Helper to simulate answers for the chat interface in development
export function simulateAiResponse(
  userQuery: string, 
  jurisdiction: 'central' | 'state', 
  stateName: string | null
): { content: string; citations: Citation[] } {
  const query = userQuery.toLowerCase();

  // Route 1: Ayushman Bharat
  if (query.includes('ayushman') || query.includes('pmjay') || query.includes('pm-jay') || query.includes('health cover')) {
    return {
      content: 'Under **Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY)**, eligible beneficiaries receive a health cover of up to **₹5,00,000 per family per year** for secondary and tertiary care hospitalization. \n\n### Eligibility Criteria:\n- Identified rural households with deprivation indicators (e.g. kucha houses, manual labor).\n- Specified urban occupation categories (e.g. sanitation workers, ragpickers).\n- Eligible families list is drawn from the SECC-2011 database.\n\n### Application Requirements:\n- **Identity verification**: Aadhaar Card or Voter ID is required at the time of register/hospital admission.\n- **E-Card generation**: You can generate your Ayushman Card at any empaneled hospital or Common Service Centre (CSC).',
      citations: [
        {
          act: 'National Health Agency Operational Manual',
          section: 'Section 4.1',
          jurisdiction: 'Central',
          excerpt: 'PM-JAY shall provide health insurance cover of Rs. 5 Lakhs per family per year for secondary and tertiary hospitalization to poor and vulnerable families.',
          source_url: 'https://pmjay.gov.in/',
          retrieval_scores: {
            dense: 0.884,
            bm25: 7.412,
            rrf: 0.03279
          }
        }
      ]
    };
  }

  // Route 2: RTI / Right to Information
  if (query.includes('rti') || query.includes('right to information') || query.includes('thirty days') || query.includes('respond')) {
    return {
      content: 'Under the **Right to Information (RTI) Act, 2005**, authorities have strict statutory timelines to dispose of requests for information:\n\n1. **Standard response time**: **30 days** from the receipt of the application.\n2. **Urgent cases**: If the information requested concerns the **life or liberty of a person**, the response must be delivered within **48 hours**.\n3. **Assistant PIO delay**: An additional 5 days is permitted if the request is routed through an Assistant PIO.',
      citations: [
        {
          act: 'Right to Information Act, 2005',
          section: 'Section 7(1)',
          jurisdiction: 'Central',
          excerpt: '...expeditiously as possible, and in any case within thirty days of the receipt of the request: Provided that where the information sought for concerns the life or liberty of a person, the same shall be provided within forty-eight hours...',
          source_url: 'https://www.indiacode.nic.in/handle/123456789/2065',
          retrieval_scores: {
            dense: 0.912,
            bm25: 8.330,
            rrf: 0.03279
          }
        }
      ]
    };
  }

  // Route 3: PM-Kisan
  if (query.includes('kisan') || query.includes('farmer') || query.includes('pm-kisan')) {
    return {
      content: 'The **Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)** provides income support to landholding farmers across India:\n\n- **Support amount**: **₹6,000 per year** paid in three equal installments of ₹2,000.\n- **Eligibility**: All landholding families who own cultivable land (excluding institutional landholders and tax-paying individuals).\n- **Transfer mode**: Directly to bank accounts through Aadhaar-seeded DBT systems.',
      citations: [
        {
          act: 'PM-Kisan Operational Guidelines',
          section: 'Paragraph 3',
          jurisdiction: 'Central',
          excerpt: 'Under the scheme, direct payment of Rs 6000 per year will be provided in three equal installments of Rs. 2000 each directly into the bank accounts of beneficiaries.',
          source_url: 'https://www.myscheme.gov.in/schemes/pm-kisan'
        }
      ]
    };
  }

  // Route 4: Default General Response
  const contextString = stateName ? `focused on ${stateName} (${jurisdiction} jurisdiction)` : 'focused on central jurisdiction';
  return {
    content: `Thank you for your question about Indian civic resources. I am currently running in **offline/API-ready mode** ${contextString}.\n\nTo see detailed verification flows, you can ask about:\n- **"What is Ayushman Bharat?"** (Health Insurance scheme details and documents)\n- **"How does RTI request work?"** (Legal timelines and Section 7 parameters)\n- **"What is the PM-Kisan scheme?"** (Income support for farmers)\n\nAlternatively, you can explore the directories directly by selecting **Welfare Schemes** or **Legal Acts** in the sidebar.`,
    citations: []
  };
}
