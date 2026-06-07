export const sectionLabels = {
  header: 'Шапка сайта',
  hero: 'Hero-блок',
  simple_words: 'Об игре Лила',
  about: 'О проекте',
  guide: 'О проекте и проводнике',
  benefits: 'Преимущества',
  advantages: 'Преимущества',
  meditations: 'Медитации',
  meditation: 'Медитации',
  leela: 'Игра Лила',
  leela_game: 'Игра Лила',
  gallery: 'Галерея',
  reviews: 'Отзывы',
  services: 'Форматы занятий',
  formats: 'Форматы занятий',
  contacts: 'Форма заявки и контакты',
  contact_form: 'Форма заявки',
  lead_form: 'Форма заявки',
  footer: 'Подвал сайта',
}

export function getSectionLabel(section) {
  return section?.display_title
    || sectionLabels[section?.key]
    || sectionLabels[section?.section_type]
    || section?.title
    || 'Раздел сайта'
}
