export interface ClaimForm {
  description: string;
  principal_amount: string;
  default_date: string;
  invoice_number: string;
  invoice_date: string;
  rate_basis: string;
}

export const EMPTY_CLAIM: ClaimForm = {
  description: "",
  principal_amount: "",
  default_date: "",
  invoice_number: "",
  invoice_date: "",
  rate_basis: "yearly",
};

export interface InlineContact {
  contact_type: "company" | "person";
  name: string;
  email: string;
  phone: string;
  kvk_number: string;
  btw_number: string;
  visit_address: string;
  visit_postcode: string;
  visit_city: string;
  postal_address: string;
  postal_postcode: string;
  postal_city: string;
}

export const EMPTY_INLINE_CONTACT: InlineContact = {
  contact_type: "company",
  name: "",
  email: "",
  phone: "",
  kvk_number: "",
  btw_number: "",
  visit_address: "",
  visit_postcode: "",
  visit_city: "",
  postal_address: "",
  postal_postcode: "",
  postal_city: "",
};
