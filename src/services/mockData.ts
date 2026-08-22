import type { Conversation, WelfareScheme, LegalAct, Citation } from './api';

export const mockConversations: Conversation[] = [
  {
    id: 'conv_1',
    title: 'Ayushman Bharat Eligibility',
    jurisdiction: 'central',
    stateName: null,
    timestamp: '10:15 AM',
    messages: [
      {
        id: 'm1',
        role: 'user',
        content: 'Who is eligible for Ayushman Bharat (PM-JAY) and what documents do I need to apply?',
        timestamp: '10:14 AM'
      },
      {
        id: 'm2',
        role: 'assistant',
        content: 'Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY) is a central government scheme providing a health cover of up to ₹5 Lakh per family per year for secondary and tertiary care hospitalization. \n\n### 1. Eligibility Criteria:\n- **Rural Families**: Households living in one-room houses with kucha walls, female-headed households, households with no adult member between ages 16-59, SC/ST households, and landless households deriving major income from manual casual labor.\n- **Urban Families**: Specific occupational categories including ragpickers, beggars, domestic workers, street vendors, construction workers, plumbers, sweepers, and transport workers.\n- **Automatic Inclusion**: Households listed in the SECC 2011 database, bonded laborers, and families residing in primitive tribal groups.\n\n### 2. Required Documents:\n- **Identity Proof**: Aadhaar Card, PAN Card, or Driving License.\n- **Address Proof**: Ration Card, Utility Bills, or Voter ID.\n- **Income/Caste Certificate**: Required to prove eligibility if selected under socio-economic categories.',
        timestamp: '10:15 AM',
        status: 'verified',
        citations: [
          {
            id: 'cit_1',
            actName: 'National Health Agency Operational Guidelines',
            sectionNumber: 'Section 4.2',
            jurisdiction: 'Central',
            verified: true,
            excerpt: 'The target beneficiaries under PM-JAY are identified based on select deprivation criteria in rural areas and occupational criteria in urban areas as per the Socio-Economic Caste Census (SECC) database.',
            sourceUrl: 'https://pmjay.gov.in/'
          },
          {
            id: 'cit_2',
            actName: 'Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act',
            sectionNumber: 'Section 7',
            jurisdiction: 'Central',
            verified: true,
            excerpt: 'The Central Government or State Government may require that an individual undergo authentication or furnish proof of possession of Aadhaar number as a condition for receiving subsidy, benefit or service.',
            sourceUrl: 'https://uidai.gov.in/'
          }
        ],
        feedback: 'helpful'
      }
    ]
  },
  {
    id: 'conv_2',
    title: 'RTI Request Process',
    jurisdiction: 'central',
    stateName: null,
    timestamp: 'Yesterday',
    messages: [
      {
        id: 'm3',
        role: 'user',
        content: 'How many days does an authority have to respond to an RTI application?',
        timestamp: 'Yesterday'
      },
      {
        id: 'm4',
        role: 'assistant',
        content: 'Under the Right to Information (RTI) Act, 2005, a Public Information Officer (PIO) is bound by strict timelines to respond to requests:\n\n1. **Standard Requests**: The response must be provided within **30 days** of receipt of the application.\n2. **Assistant PIO Requests**: If the application is submitted to an Assistant PIO, the response timeline is extended by 5 days, totaling **35 days**.\n3. **Life and Liberty**: If the information sought concerns the **life or liberty of a person**, the PIO must respond within **48 hours**.',
        timestamp: 'Yesterday',
        status: 'verified',
        citations: [
          {
            id: 'cit_3',
            actName: 'Right to Information Act, 2005',
            sectionNumber: 'Section 7(1)',
            jurisdiction: 'Central',
            verified: true,
            excerpt: 'Subject to the proviso to sub-section (2) of section 5 or the proviso to sub-section (3) of section 6, the Central Public Information Officer or State Public Information Officer, as the case may be, on receipt of a request under section 6 shall, as expeditiously as possible, and in any case within thirty days of the receipt of the request, either provide the information on payment of such fee as may be prescribed or reject the request for any of the reasons specified in sections 8 and 9: Provided that where the information sought for concerns the life or liberty of a person, the same shall be provided within forty-eight hours of the receipt of the request.',
            sourceUrl: 'https://rti.gov.in/'
          }
        ]
      }
    ]
  }
];

export const mockWelfareSchemes: WelfareScheme[] = [
  {
    id: 'scheme_1',
    name: 'Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
    description: 'The largest health assurance scheme in the world, aiming to provide free health cover of ₹5 Lakh per family per year for secondary and tertiary care hospitalization to over 12 crore poor and vulnerable families.',
    eligibility: 'Identified households under rural and urban categories from SECC 2011 database, including landless laborers, female-headed households, SC/ST, and informal workers.',
    benefits: 'Cashless cover of up to ₹5,00,000 per family per year for medical treatment, hospital stay, pre/post-hospitalization expenses, and medicines.',
    requiredDocuments: ['Aadhaar Card', 'Ration Card / PM-JAY Letter', 'Active Mobile Number', 'Identity Proof (PAN/Voter ID)'],
    state: 'Central',
    category: 'Healthcare',
    applicationProcess: 'Verify eligibility on the PM-JAY website or visit the nearest Common Service Centre (CSC) / empaneled hospital. Register with Aadhaar, receive Ayushman Card, and claim cashless benefits directly at hospitals.',
    sources: [
      {
        id: 'cit_pmjay_1',
        actName: 'National Health Agency Guidelines',
        sectionNumber: 'Chapter 2: Beneficiary Identification',
        jurisdiction: 'Central',
        verified: true,
        excerpt: 'Beneficiary families are entitled to premium-free hospitalization coverage up to rupees five lakh per annum per family on a family floater basis.'
      }
    ]
  },
  {
    id: 'scheme_2',
    name: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
    description: 'A central sector scheme providing income support of ₹6,000 per year in three equal installments of ₹2,000 to all landholding farmer families across the country.',
    eligibility: 'All landholding farmer families with cultivable landholdings in their names (subject to certain exclusion criteria for higher-income groups).',
    benefits: 'Direct financial assistance of ₹6,000 per year, directly transferred to bank accounts via Direct Benefit Transfer (DBT).',
    requiredDocuments: ['Aadhaar Card (Mandatory)', 'Land ownership documents (Khatouni)', 'Bank Account Details', 'Mobile Number'],
    state: 'Central',
    category: 'Agriculture',
    applicationProcess: 'Apply online at the PM-Kisan portal (pmkisan.gov.in) through Farmer Corner, or visit a local Common Service Centre (CSC). Self-registration is validated by state agricultural officers.',
    sources: [
      {
        id: 'cit_pmkisan_1',
        actName: 'PM-Kisan Operational Guidelines',
        sectionNumber: 'Paragraph 3: Eligibility & Exclusions',
        jurisdiction: 'Central',
        verified: true,
        excerpt: 'Under the scheme, financial benefit of Rs.6000/- per year per family is to be given to all landholder farmer families.'
      }
    ]
  },
  {
    id: 'scheme_3',
    name: 'Sanjay Gandhi Niradhar Pension Scheme',
    description: 'A state government welfare scheme in Maharashtra offering monthly financial aid/pension to destitute persons, disabled individuals, widows, and those suffering from critical illnesses.',
    eligibility: 'Residents of Maharashtra, age below 65 (for destitute), family annual income below ₹21,000, and meeting criteria for disability (40%+), widowhood, or orphan status.',
    benefits: 'Monthly financial pension of ₹1,000 to ₹1,500 depending on the number of dependents in the family.',
    requiredDocuments: ['Age Proof Certificate', 'Income Certificate (Tahsildar)', 'Disability Certificate (if applicable)', 'Maharashtra Domicile Certificate', 'Bank Passbook'],
    state: 'Maharashtra',
    category: 'Social Welfare & Pension',
    applicationProcess: 'Collect Form A from the Tahsildar Office or download it from the Maharashtra government portal. Submit form with domicile, income, and eligibility certificates to the Tahsildar / Collector office for committee approval.',
    sources: [
      {
        id: 'cit_sgn_1',
        actName: 'Maharashtra Social Justice Department Resolution',
        sectionNumber: 'Section 1.1: destitutes',
        jurisdiction: 'Maharashtra',
        verified: true,
        excerpt: 'Destitute persons who are unable to work, blind, disabled, widows, or suffer from long term major illness are eligible for a monthly assistance of Rs 1,000.'
      }
    ]
  }
];

export const mockLegalActs: LegalAct[] = [
  {
    id: 'act_1',
    name: 'The Right to Information Act, 2005',
    description: 'An Act to provide for setting out the practical regime of right to information for citizens to secure access to information under the control of public authorities, in order to promote transparency and accountability.',
    jurisdiction: 'central',
    sections: [
      {
        number: 'Section 4',
        title: 'Obligations of Public Authorities',
        content: 'Every public authority shall maintain all its records duly catalogued and indexed and publish details of its organization, functions, duties, and officers, ensuring maximum proactive disclosure of information.'
      },
      {
        number: 'Section 6',
        title: 'Request for Obtaining Information',
        content: 'A person who desires to obtain any information under this Act shall make a request in writing or through electronic means in English or Hindi or in the official language of the area, accompanying such fee as may be prescribed.'
      },
      {
        number: 'Section 7',
        title: 'Disposal of Request',
        content: 'A Central Public Information Officer or State Public Information Officer shall respond to requests as expeditiously as possible, and in any case within thirty days of the receipt of the request, or within forty-eight hours if it concerns the life or liberty of a person.'
      }
    ]
  },
  {
    id: 'act_2',
    name: 'The Bharatiya Nyaya Sanhita, 2023',
    description: 'The official criminal code of India, replacing the colonial-era Indian Penal Code (IPC) to reform and modernize the justice administration system.',
    jurisdiction: 'central',
    sections: [
      {
        number: 'Section 1',
        title: 'Short Title, Commencement and Application',
        content: 'This Sanhita may be called the Bharatiya Nyaya Sanhita, 2023, and it shall come into force on such date as the Central Government may appoint.'
      },
      {
        number: 'Section 3(5)',
        title: 'Joint Liability',
        content: 'When a criminal act is done by several persons in furtherance of the common intention of all, each of such persons is liable for that act in the same manner as if it were done by him alone.'
      }
    ]
  }
];

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
          id: 'cit_sim_pm_1',
          actName: 'National Health Agency Operational Manual',
          sectionNumber: 'Section 4.1',
          jurisdiction: 'Central',
          verified: true,
          excerpt: 'PM-JAY shall provide health insurance cover of Rs. 5 Lakhs per family per year for secondary and tertiary hospitalization to poor and vulnerable families.',
          sourceUrl: 'https://pmjay.gov.in/'
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
          id: 'cit_sim_rti_1',
          actName: 'Right to Information Act, 2005',
          sectionNumber: 'Section 7(1)',
          jurisdiction: 'Central',
          verified: true,
          excerpt: '...expeditiously as possible, and in any case within thirty days of the receipt of the request: Provided that where the information sought for concerns the life or liberty of a person, the same shall be provided within forty-eight hours...',
          sourceUrl: 'https://rti.gov.in/'
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
          id: 'cit_sim_kisan_1',
          actName: 'PM-Kisan Operational Guidelines',
          sectionNumber: 'Paragraph 3',
          jurisdiction: 'Central',
          verified: true,
          excerpt: 'Under the scheme, direct payment of Rs 6000 per year will be provided in three equal installments of Rs. 2000 each directly into the bank accounts of beneficiaries.',
          sourceUrl: 'https://pmkisan.gov.in/'
        }
      ]
    };
  }

  // Route 4: Sanjay Gandhi / Maharashtra State Specific
  if ((query.includes('sanjay') || query.includes('pension')) && stateName?.toLowerCase() === 'maharashtra') {
    return {
      content: 'In Maharashtra, the **Sanjay Gandhi Niradhar Pension Scheme** provides destitute individuals with financial support:\n\n- **Amount**: **₹1,000 per month** (increases up to ₹1,500 if there are multiple dependents).\n- **Beneficiary types**: Disabled persons, widows, orphans, and critically ill individuals under 65 years.\n- **Income ceiling**: The annual family income of the beneficiary must be below **₹21,000**.',
      citations: [
        {
          id: 'cit_sim_sgn_1',
          actName: 'Maharashtra Social Justice Department Directives',
          sectionNumber: 'Clause 2',
          jurisdiction: 'State - Maharashtra',
          verified: true,
          excerpt: 'Destitutes, widows, disabled persons are entitled to monthly pension benefits subject to Tahsildar approval of the income certificate.',
          sourceUrl: 'https://sanjaygandhiniradhar.maharashtra.gov.in/'
        }
      ]
    };
  }

  // Route 5: Default General Response notifying about backend connection
  const contextString = stateName ? `focused on ${stateName} (${jurisdiction} jurisdiction)` : 'focused on central jurisdiction';
  return {
    content: `Thank you for your question about Indian civic resources. I am currently running in **offline/API-ready mode** ${contextString}.\n\nTo see detailed verification flows, you can ask about:\n- **"What is Ayushman Bharat?"** (Health Insurance scheme details and documents)\n- **"How does RTI request work?"** (Legal timelines and Section 7 parameters)\n- **"What is the PM-Kisan scheme?"** (Income support for farmers)\n\nAlternatively, you can explore the directories directly by selecting **Welfare Schemes** or **Legal Acts** in the sidebar. Once the FastAPI RAG backend is connected, this screen will display real-time answers retrieved dynamically from indexed government portals and laws.`,
    citations: []
  };
}
